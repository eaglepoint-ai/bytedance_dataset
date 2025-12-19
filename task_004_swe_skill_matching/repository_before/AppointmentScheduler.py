from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import math
from typing import Iterable, List, Optional, Tuple


class AppointmentPriority(Enum):
    NORMAL = "Normal"
    URGENT = "Urgent"


class AppointmentType(Enum):
    CONSULTATION = "Consultation"
    FOLLOW_UP = "FollowUp"
    PROCEDURE = "Procedure"


@dataclass
class AppointmentRequest:
    patient_id: int
    specialty: str
    preferred_date: datetime
    duration: timedelta
    preferred_time: Optional[timedelta] = None
    preferred_provider_id: Optional[int] = None
    previous_provider_id: Optional[int] = None
    priority: AppointmentPriority = AppointmentPriority.NORMAL
    appointment_type: AppointmentType = AppointmentType.CONSULTATION
    insurance_plan: str = "Standard"


@dataclass
class ProviderAvailability:
    start: datetime
    end: datetime


@dataclass
class Appointment:
    id: int
    provider_id: int
    patient_id: int
    start_time: datetime
    duration: timedelta
    priority: AppointmentPriority = AppointmentPriority.NORMAL
    appointment_type: AppointmentType = AppointmentType.CONSULTATION
    provider: Optional["Provider"] = None

    @property
    def end_time(self) -> datetime:
        return self.start_time + self.duration


@dataclass
class Provider:
    id: int
    name: str
    specialties: List[str] = field(default_factory=list)
    accepted_insurances: List[str] = field(default_factory=list)
    rating: float = 3.5
    availability: List[ProviderAvailability] = field(default_factory=list)
    appointments: List[Appointment] = field(default_factory=list)


@dataclass
class PatientHistory:
    patient_id: int
    missed_appointments: int
    last_visit: Optional[datetime]


@dataclass
class ScheduleResult:
    success: bool = False
    requires_insurance_approval: bool = False
    requires_deposit: bool = False
    estimated_cost: Decimal = Decimal("0.00")
    deposit_amount: Decimal = Decimal("0.00")
    provider: Optional[Provider] = None
    scheduled_time: Optional[datetime] = None
    warnings: List[str] = field(default_factory=list)
    suggested_dates: List[datetime] = field(default_factory=list)

    def add_warning(self, warning: str) -> None:
        if warning and warning.strip():
            self.warnings.append(warning.strip())


class NoAvailableProvidersException(Exception):
    pass


class InvalidDurationException(Exception):
    pass


class AppointmentScheduler:
    _ALTERNATIVE_DAY_SEARCH_WINDOW = 7
    _MAX_SCHEDULE_SEARCH_DAYS = 30

    def schedule_appointment(
        self,
        request: AppointmentRequest,
        available_providers: List[Provider],
    ) -> ScheduleResult:
        if request is None:
            raise ValueError("request is required")
        if available_providers is None:
            raise ValueError("available_providers is required")

        result = ScheduleResult()

        eligible_providers = [
            provider
            for provider in available_providers
            if any(s.lower() == request.specialty.lower() for s in provider.specialties)
            and self._is_provider_available(provider, request.preferred_date, request.duration)
        ]

        if not eligible_providers:
            alternative_dates = self._find_alternative_dates(request)
            if alternative_dates:
                result.suggested_dates = alternative_dates
                return result
            raise NoAvailableProvidersException("No providers available for the request.")

        selected_provider = self._pick_patient_preferred_provider(
            eligible_providers, request.preferred_provider_id, request.previous_provider_id
        )

        if selected_provider is None:
            selected_provider = self._select_provider_by_criteria(eligible_providers, request)

        if request.preferred_time is not None:
            scheduled_time = self._find_nearest_available_slot(
                selected_provider,
                request.preferred_date,
                request.preferred_time,
                request.duration,
            )
        else:
            scheduled_time = self._find_best_available_slot(
                selected_provider,
                request.preferred_date,
                request.duration,
                request.patient_id,
            )

        if request.priority == AppointmentPriority.URGENT:
            conflicts = self._get_conflicting_appointments(selected_provider, scheduled_time, request.duration)
            if conflicts:
                if self._can_reschedule_conflicts(conflicts):
                    self._reschedule_appointments(conflicts)
                else:
                    sooner_provider = self._find_sooner_provider(eligible_providers, request, scheduled_time)
                    if sooner_provider is not None:
                        selected_provider = sooner_provider
                        scheduled_time = self._find_best_available_slot(
                            selected_provider,
                            request.preferred_date,
                            request.duration,
                            request.patient_id,
                        )

        if not self._is_insurance_valid(request.patient_id, selected_provider.id, request.specialty):
            result.requires_insurance_approval = True
            result.estimated_cost = self._calculate_estimated_cost(request, selected_provider)

        if request.appointment_type == AppointmentType.CONSULTATION and request.duration < timedelta(minutes=30):
            raise InvalidDurationException("Consultations require at least 30 minutes")
        if request.appointment_type == AppointmentType.FOLLOW_UP and request.duration > timedelta(minutes=15):
            result.add_warning("Follow-up appointments typically take 15 minutes.")

        history = self._get_patient_history(request.patient_id)
        if history.missed_appointments >= 3:
            result.requires_deposit = True
            result.deposit_amount = self._calculate_deposit_amount(request)

        result.success = True
        result.provider = selected_provider
        result.scheduled_time = scheduled_time
        return result

    def _is_provider_available(self, provider: Provider, date: datetime, duration: timedelta) -> bool:
        if provider is None:
            return False

        requested_end = date + duration
        has_availability = any(window.start <= date and window.end >= requested_end for window in provider.availability)
        if not has_availability:
            return False

        return not any(
            self._are_overlapping(appt.start_time, appt.end_time, date, requested_end)
            for appt in provider.appointments
        )

    def _find_alternative_dates(self, request: AppointmentRequest) -> List[datetime]:
        suggestions: List[datetime] = []
        preferred_time = request.preferred_time or timedelta(hours=9)
        cursor = self._midnight(request.preferred_date) + timedelta(days=1)

        while len(suggestions) < self._ALTERNATIVE_DAY_SEARCH_WINDOW:
            if cursor.weekday() < 5:
                suggestions.append(cursor + preferred_time)
            cursor += timedelta(days=1)

        return suggestions

    def _select_provider_by_criteria(
        self,
        providers: List[Provider],
        request: AppointmentRequest,
    ) -> Provider:
        return sorted(
            providers,
            key=lambda p: (
                -p.rating,
                len(p.appointments),
                self._get_next_availability_start(p, request.preferred_date) or datetime.max,
            ),
        )[0]

    def _pick_patient_preferred_provider(
        self,
        providers: List[Provider],
        preferred_provider_id: Optional[int],
        previous_provider_id: Optional[int],
    ) -> Optional[Provider]:
        provider_map = {provider.id: provider for provider in providers}
        if preferred_provider_id is not None and preferred_provider_id in provider_map:
            return provider_map[preferred_provider_id]
        if previous_provider_id is not None and previous_provider_id in provider_map:
            return provider_map[previous_provider_id]
        return None

    def _find_nearest_available_slot(
        self,
        provider: Provider,
        date: datetime,
        preferred_time: timedelta,
        duration: timedelta,
    ) -> datetime:
        target = self._midnight(date) + preferred_time
        best_candidate = None
        best_distance = None

        for offset in range(self._MAX_SCHEDULE_SEARCH_DAYS):
            day = self._midnight(date) + timedelta(days=offset)
            slots = list(self._get_free_slots(provider, day))

            for slot_start, slot_end in slots:
                if slot_end - slot_start < duration:
                    continue

                candidate = slot_start
                if day == self._midnight(date) and slot_start <= target and target + duration <= slot_end:
                    candidate = target

                distance = abs((candidate - target).total_seconds())
                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_candidate = candidate

            if best_distance == 0:
                break

        return best_candidate or target

    def _find_best_available_slot(
        self,
        provider: Provider,
        preferred_date: datetime,
        duration: timedelta,
        patient_id: int,
    ) -> datetime:
        for offset in range(self._MAX_SCHEDULE_SEARCH_DAYS):
            day = self._midnight(preferred_date) + timedelta(days=offset)
            for slot_start, slot_end in self._get_free_slots(provider, day):
                if slot_end - slot_start >= duration:
                    return slot_start

        return self._midnight(preferred_date) + timedelta(hours=(patient_id % 5) + 8)

    def _get_conflicting_appointments(
        self,
        provider: Provider,
        start: datetime,
        duration: timedelta,
    ) -> List[Appointment]:
        end = start + duration
        conflicts: List[Appointment] = []

        for appointment in provider.appointments:
            if self._are_overlapping(appointment.start_time, appointment.end_time, start, end):
                appointment.provider = provider
                conflicts.append(appointment)

        return conflicts

    def _can_reschedule_conflicts(self, conflicts: List[Appointment]) -> bool:
        if not conflicts:
            return True
        threshold = datetime.now() + timedelta(hours=2)
        return all(appt.priority != AppointmentPriority.URGENT and appt.start_time > threshold for appt in conflicts)

    def _reschedule_appointments(self, conflicts: List[Appointment]) -> None:
        for appointment in sorted(conflicts, key=lambda a: a.start_time):
            if appointment.provider is None:
                continue
            new_start = self._find_best_available_slot(
                appointment.provider,
                appointment.start_time + timedelta(hours=1),
                appointment.duration,
                appointment.patient_id,
            )
            appointment.start_time = new_start

    def _find_sooner_provider(
        self,
        providers: List[Provider],
        request: AppointmentRequest,
        current_scheduled_time: datetime,
    ) -> Optional[Provider]:
        best_provider = None
        best_slot = current_scheduled_time

        for provider in providers:
            slot = self._find_best_available_slot(provider, request.preferred_date, request.duration, request.patient_id)
            if slot < best_slot:
                best_slot = slot
                best_provider = provider

        return best_provider

    def _is_insurance_valid(self, patient_id: int, provider_id: int, specialty: str) -> bool:
        checksum = patient_id + provider_id + len(specialty)
        return checksum % 5 != 0

    def _calculate_estimated_cost(self, request: AppointmentRequest, provider: Provider) -> Decimal:
        base_rate = {
            AppointmentType.CONSULTATION: Decimal("150"),
            AppointmentType.FOLLOW_UP: Decimal("80"),
            AppointmentType.PROCEDURE: Decimal("400"),
        }.get(request.appointment_type, Decimal("120"))

        duration_multiplier = Decimal(request.duration.total_seconds() / 60) / Decimal(30)
        rating_adjustment = Decimal(provider.rating / 5.0)
        return (base_rate * duration_multiplier * max(Decimal("0.5"), rating_adjustment)).quantize(Decimal("0.01"))

    def _get_patient_history(self, patient_id: int) -> PatientHistory:
        missed = abs(patient_id % 4)
        last_visit = datetime.today() - timedelta(days=patient_id % 60)
        return PatientHistory(patient_id=patient_id, missed_appointments=missed, last_visit=last_visit)

    def _calculate_deposit_amount(self, request: AppointmentRequest) -> Decimal:
        base_amount = Decimal("150") if request.appointment_type == AppointmentType.PROCEDURE else Decimal("50")
        duration_hours = Decimal(math.ceil(request.duration.total_seconds() / 3600))
        return base_amount + (duration_hours * Decimal("25"))

    @staticmethod
    def _are_overlapping(
        first_start: datetime,
        first_end: datetime,
        second_start: datetime,
        second_end: datetime,
    ) -> bool:
        return first_start < second_end and second_start < first_end

    def _get_free_slots(self, provider: Provider, date: datetime) -> Iterable[Tuple[datetime, datetime]]:
        day_start = self._midnight(date)
        day_end = day_start + timedelta(days=1)

        windows = sorted(
            (
                ProviderAvailability(
                    start=max(window.start, day_start),
                    end=min(window.end, day_end),
                )
                for window in provider.availability
                if self._are_overlapping(window.start, window.end, day_start, day_end)
            ),
            key=lambda window: window.start,
        )

        for window in windows:
            busy_slots = sorted(
                (
                    appointment
                    for appointment in provider.appointments
                    if self._are_overlapping(appointment.start_time, appointment.end_time, window.start, window.end)
                ),
                key=lambda appt: appt.start_time,
            )

            cursor = window.start
            for appointment in busy_slots:
                if appointment.start_time > cursor:
                    yield cursor, appointment.start_time
                if appointment.end_time > cursor:
                    cursor = appointment.end_time

            if cursor < window.end:
                yield cursor, window.end

    def _get_next_availability_start(self, provider: Provider, from_date: datetime) -> Optional[datetime]:
        for offset in range(self._MAX_SCHEDULE_SEARCH_DAYS):
            date = self._midnight(from_date) + timedelta(days=offset)
            for slot_start, _ in self._get_free_slots(provider, date):
                return slot_start
        return None

    @staticmethod
    def _midnight(moment: datetime) -> datetime:
        return datetime(moment.year, moment.month, moment.day)
