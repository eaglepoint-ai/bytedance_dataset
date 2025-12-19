using System;
using System.Collections.Generic;
using System.Linq;

namespace repository_before
{
    public enum AppointmentPriority
    {
        Normal,
        Urgent
    }

    public enum AppointmentType
    {
        Consultation,
        FollowUp,
        Procedure
    }

    public class AppointmentRequest
    {
        public int PatientId { get; set; }
        public string Specialty { get; set; } = string.Empty;
        public DateTime PreferredDate { get; set; }
        public TimeSpan Duration { get; set; }
        public TimeSpan? PreferredTime { get; set; }
        public int? PreferredProviderId { get; set; }
        public int? PreviousProviderId { get; set; }
        public AppointmentPriority Priority { get; set; } = AppointmentPriority.Normal;
        public AppointmentType AppointmentType { get; set; } = AppointmentType.Consultation;
        public string InsurancePlan { get; set; } = "Standard";
    }

    public class ProviderAvailability
    {
        public DateTime Start { get; set; }
        public DateTime End { get; set; }
    }

    public class Appointment
    {
        public int Id { get; set; }
        public int ProviderId { get; set; }
        public int PatientId { get; set; }
        public DateTime StartTime { get; set; }
        public TimeSpan Duration { get; set; }
        public AppointmentPriority Priority { get; set; } = AppointmentPriority.Normal;
        public AppointmentType AppointmentType { get; set; } = AppointmentType.Consultation;
        public Provider Provider { get; set; }
        public DateTime EndTime => StartTime + Duration;
    }

    public class Provider
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public List<string> Specialties { get; set; } = new List<string>();
        public List<string> AcceptedInsurances { get; set; } = new List<string>();
        public double Rating { get; set; } = 3.5;
        public List<ProviderAvailability> Availability { get; set; } = new List<ProviderAvailability>();
        public List<Appointment> Appointments { get; set; } = new List<Appointment>();
    }

    public class PatientHistory
    {
        public int PatientId { get; set; }
        public int MissedAppointments { get; set; }
        public DateTime? LastVisit { get; set; }
    }

    public class ScheduleResult
    {
        public bool Success { get; set; }
        public bool RequiresInsuranceApproval { get; set; }
        public bool RequiresDeposit { get; set; }
        public decimal EstimatedCost { get; set; }
        public decimal DepositAmount { get; set; }
        public Provider Provider { get; set; }
        public DateTime ScheduledTime { get; set; }
        public List<string> Warnings { get; } = new List<string>();
        public List<DateTime> SuggestedDates { get; set; } = new List<DateTime>();

        public void AddWarning(string warning)
        {
            if (!string.IsNullOrWhiteSpace(warning))
            {
                Warnings.Add(warning);
            }
        }
    }

    public class NoAvailableProvidersException : Exception
    {
        public NoAvailableProvidersException()
            : base("No providers are available for the requested specialty and date.")
        {
        }
    }

    public class InvalidDurationException : Exception
    {
        public InvalidDurationException(string message) : base(message)
        {
        }
    }

    public class AppointmentScheduler
    {
        private const int AlternativeDaySearchWindow = 7;
        private const int MaxScheduleSearchDays = 30;

        public ScheduleResult ScheduleAppointment(AppointmentRequest request,
                                                  List<Provider> availableProviders)
        {
            if (request == null)
            {
                throw new ArgumentNullException(nameof(request));
            }

            if (availableProviders == null)
            {
                throw new ArgumentNullException(nameof(availableProviders));
            }

            var result = new ScheduleResult();

            var eligibleProviders = availableProviders
                .Where(p => p.Specialties.Any(s => string.Equals(s, request.Specialty, StringComparison.OrdinalIgnoreCase)))
                .Where(p => IsProviderAvailable(p, request.PreferredDate, request.Duration))
                .ToList();

            if (!eligibleProviders.Any())
            {
                var alternativeDates = FindAlternativeDates(request);
                if (alternativeDates.Any())
                {
                    result.SuggestedDates = alternativeDates;
                    return result;
                }

                throw new NoAvailableProvidersException();
            }

            Provider selectedProvider = null;
            if (request.PreferredProviderId.HasValue)
            {
                selectedProvider = eligibleProviders
                    .FirstOrDefault(p => p.Id == request.PreferredProviderId.Value);
            }

            if (selectedProvider == null && request.PreviousProviderId.HasValue)
            {
                selectedProvider = eligibleProviders
                    .FirstOrDefault(p => p.Id == request.PreviousProviderId.Value);
            }

            if (selectedProvider == null)
            {
                selectedProvider = SelectProviderByCriteria(eligibleProviders, request);
            }

            DateTime scheduledTime;
            if (request.PreferredTime.HasValue)
            {
                scheduledTime = FindNearestAvailableSlot(
                    selectedProvider,
                    request.PreferredDate,
                    request.PreferredTime.Value,
                    request.Duration);
            }
            else
            {
                scheduledTime = FindBestAvailableSlot(
                    selectedProvider,
                    request.PreferredDate,
                    request.Duration,
                    request.PatientId);
            }

            if (request.Priority == AppointmentPriority.Urgent)
            {
                var conflictingAppointments = GetConflictingAppointments(
                    selectedProvider, scheduledTime, request.Duration);

                if (conflictingAppointments.Any())
                {
                    if (CanRescheduleConflicts(conflictingAppointments))
                    {
                        RescheduleAppointments(conflictingAppointments);
                    }
                    else
                    {
                        var soonerProvider = FindSoonerProvider(
                            eligibleProviders, request, scheduledTime);

                        if (soonerProvider != null)
                        {
                            selectedProvider = soonerProvider;
                            scheduledTime = FindBestAvailableSlot(
                                selectedProvider, request.PreferredDate,
                                request.Duration, request.PatientId);
                        }
                    }
                }
            }

            if (!IsInsuranceValid(request.PatientId, selectedProvider.Id, request.Specialty))
            {
                result.RequiresInsuranceApproval = true;
                result.EstimatedCost = CalculateEstimatedCost(request, selectedProvider);
            }

            if (request.AppointmentType == AppointmentType.Consultation &&
                request.Duration < TimeSpan.FromMinutes(30))
            {
                throw new InvalidDurationException("Consultations require at least 30 minutes");
            }
            else if (request.AppointmentType == AppointmentType.FollowUp &&
                     request.Duration > TimeSpan.FromMinutes(15))
            {
                result.AddWarning("Follow-up appointments typically take 15 minutes.");
            }

            var patientHistory = GetPatientHistory(request.PatientId);
            if (patientHistory.MissedAppointments >= 3)
            {
                result.RequiresDeposit = true;
                result.DepositAmount = CalculateDepositAmount(request);
            }

            result.Success = true;
            result.Provider = selectedProvider;
            result.ScheduledTime = scheduledTime;

            return result;
        }

        private bool IsProviderAvailable(Provider provider, DateTime date, TimeSpan duration)
        {
            if (provider == null)
            {
                return false;
            }

            var requestedEnd = date + duration;
            var availabilityWindow = provider.Availability
                .FirstOrDefault(window => window.Start <= date && window.End >= requestedEnd);

            if (availabilityWindow == null)
            {
                return false;
            }

            return !provider.Appointments.Any(appointment =>
                AreOverlapping(appointment.StartTime, appointment.EndTime, date, requestedEnd));
        }

        private List<DateTime> FindAlternativeDates(AppointmentRequest request)
        {
            var suggestions = new List<DateTime>();
            var preferredTime = request.PreferredTime ?? TimeSpan.FromHours(9);
            var cursor = request.PreferredDate.Date.AddDays(1);

            while (suggestions.Count < AlternativeDaySearchWindow)
            {
                if (cursor.DayOfWeek != DayOfWeek.Saturday &&
                    cursor.DayOfWeek != DayOfWeek.Sunday)
                {
                    suggestions.Add(cursor.Add(preferredTime));
                }

                cursor = cursor.AddDays(1);
            }

            return suggestions;
        }

        private Provider SelectProviderByCriteria(List<Provider> providers,
                                                  AppointmentRequest request)
        {
            return providers
                .OrderByDescending(p => p.Rating)
                .ThenBy(p => p.Appointments.Count)
                .ThenBy(p => GetNextAvailabilityStart(p, request.PreferredDate) ?? DateTime.MaxValue)
                .First();
        }

        private DateTime FindNearestAvailableSlot(Provider provider, DateTime date,
                                                  TimeSpan preferredTime, TimeSpan duration)
        {
            var target = date.Date.Add(preferredTime);
            var bestCandidate = DateTime.MaxValue;
            var bestDistance = TimeSpan.MaxValue;

            for (int offset = 0; offset < MaxScheduleSearchDays; offset++)
            {
                var day = date.Date.AddDays(offset);
                var slots = GetFreeSlots(provider, day).ToList();

                foreach (var slot in slots)
                {
                    if (slot.end - slot.start < duration)
                    {
                        continue;
                    }

                    var candidateStart = slot.start;
                    if (day == date.Date &&
                        target >= slot.start &&
                        target + duration <= slot.end)
                    {
                        candidateStart = target;
                    }

                    var distance = (candidateStart - target).Duration();
                    if (distance < bestDistance)
                    {
                        bestDistance = distance;
                        bestCandidate = candidateStart;
                    }
                }

                if (bestDistance == TimeSpan.Zero)
                {
                    break;
                }
            }

            if (bestCandidate == DateTime.MaxValue)
            {
                return target;
            }

            return bestCandidate;
        }

        private DateTime FindBestAvailableSlot(Provider provider, DateTime preferredDate,
                                               TimeSpan duration, int patientId)
        {
            for (int offset = 0; offset < MaxScheduleSearchDays; offset++)
            {
                var day = preferredDate.Date.AddDays(offset);
                foreach (var slot in GetFreeSlots(provider, day))
                {
                    if (slot.end - slot.start < duration)
                    {
                        continue;
                    }

                    return slot.start;
                }
            }

            return preferredDate.AddHours((patientId % 5) + 8);
        }

        private List<Appointment> GetConflictingAppointments(Provider provider, DateTime start, TimeSpan duration)
        {
            var end = start + duration;
            var conflicts = provider.Appointments
                .Where(a => AreOverlapping(a.StartTime, a.EndTime, start, end))
                .Select(a =>
                {
                    a.Provider = provider;
                    return a;
                })
                .ToList();

            return conflicts;
        }

        private bool CanRescheduleConflicts(List<Appointment> conflicts)
        {
            if (!conflicts.Any())
            {
                return true;
            }

            return conflicts.All(a =>
                a.Priority != AppointmentPriority.Urgent &&
                a.StartTime > DateTime.Now.AddHours(2));
        }

        private void RescheduleAppointments(List<Appointment> conflicts)
        {
            foreach (var appointment in conflicts.OrderBy(a => a.StartTime))
            {
                var provider = appointment.Provider;
                if (provider == null)
                {
                    continue;
                }

                var newStart = FindBestAvailableSlot(
                    provider,
                    appointment.StartTime.AddHours(1),
                    appointment.Duration,
                    appointment.PatientId);

                appointment.StartTime = newStart;
            }
        }

        private Provider FindSoonerProvider(List<Provider> providers,
                                            AppointmentRequest request,
                                            DateTime currentScheduledTime)
        {
            Provider bestProvider = null;
            DateTime bestSlot = currentScheduledTime;

            foreach (var provider in providers)
            {
                var slot = FindBestAvailableSlot(provider,
                    request.PreferredDate, request.Duration, request.PatientId);

                if (slot < bestSlot)
                {
                    bestSlot = slot;
                    bestProvider = provider;
                }
            }

            return bestProvider;
        }

        private bool IsInsuranceValid(int patientId, int providerId, string specialty)
        {
            var checksum = patientId + providerId + specialty.Length;
            return checksum % 5 != 0;
        }

        private decimal CalculateEstimatedCost(AppointmentRequest request, Provider provider)
        {
            var baseRate = request.AppointmentType switch
            {
                AppointmentType.Consultation => 150m,
                AppointmentType.FollowUp => 80m,
                AppointmentType.Procedure => 400m,
                _ => 120m
            };

            var durationMultiplier = (decimal)request.Duration.TotalMinutes / 30m;
            var ratingAdjustment = (decimal)(provider.Rating / 5.0);

            return Math.Round(baseRate * durationMultiplier * Math.Max(0.5m, ratingAdjustment), 2);
        }

        private PatientHistory GetPatientHistory(int patientId)
        {
            return new PatientHistory
            {
                PatientId = patientId,
                MissedAppointments = Math.Abs(patientId % 4),
                LastVisit = DateTime.Today.AddDays(-1 * (patientId % 60))
            };
        }

        private decimal CalculateDepositAmount(AppointmentRequest request)
        {
            var baseAmount = request.AppointmentType == AppointmentType.Procedure ? 150m : 50m;
            var durationFactor = (decimal)Math.Ceiling(request.Duration.TotalHours);
            return baseAmount + (durationFactor * 25m);
        }

        private static bool AreOverlapping(DateTime firstStart, DateTime firstEnd,
                                           DateTime secondStart, DateTime secondEnd)
        {
            return firstStart < secondEnd && secondStart < firstEnd;
        }

        private IEnumerable<(DateTime start, DateTime end)> GetFreeSlots(Provider provider, DateTime date)
        {
            var dayStart = date.Date;
            var dayEnd = dayStart.AddDays(1);

            var windows = provider.Availability
                .Where(a => AreOverlapping(a.Start, a.End, dayStart, dayEnd))
                .OrderBy(a => a.Start);

            foreach (var window in windows)
            {
                var windowStart = window.Start < dayStart ? dayStart : window.Start;
                var windowEnd = window.End > dayEnd ? dayEnd : window.End;
                var busySlots = provider.Appointments
                    .Where(a => AreOverlapping(a.StartTime, a.EndTime, windowStart, windowEnd))
                    .OrderBy(a => a.StartTime)
                    .ToList();

                var cursor = windowStart;
                foreach (var appointment in busySlots)
                {
                    if (appointment.StartTime > cursor)
                    {
                        yield return (cursor, appointment.StartTime);
                    }

                    if (appointment.EndTime > cursor)
                    {
                        cursor = appointment.EndTime;
                    }
                }

                if (cursor < windowEnd)
                {
                    yield return (cursor, windowEnd);
                }
            }
        }

        private DateTime? GetNextAvailabilityStart(Provider provider, DateTime fromDate)
        {
            for (int offset = 0; offset < MaxScheduleSearchDays; offset++)
            {
                var date = fromDate.Date.AddDays(offset);
                foreach (var slot in GetFreeSlots(provider, date))
                {
                    return slot.start;
                }
            }

            return null;
        }
    }
}
