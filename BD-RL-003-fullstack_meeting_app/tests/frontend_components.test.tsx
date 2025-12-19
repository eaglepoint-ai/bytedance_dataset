/**
 * Frontend Component Tests - React Component Rendering
 * Tests REAL React component behavior (not file existence)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import React from 'react';

// Mock auth module
vi.mock('../repository_after/meeting-scheduler/web/src/lib/auth', () => ({
  login: vi.fn(),
}));

import Login from '../repository_after/meeting-scheduler/web/src/pages/Login';
import { BookingModal } from '../repository_after/meeting-scheduler/web/src/components/BookingModal';
import { SlotList, type Slot } from '../repository_after/meeting-scheduler/web/src/components/SlotList';

describe('Login Component', () => {
  it('renders email input', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    const emailInput = screen.getByTestId('login-email');
    expect(emailInput).toBeDefined();
    expect(emailInput.tagName).toBe('INPUT');
  });

  it('renders password input', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    const passwordInput = screen.getByTestId('login-password');
    expect(passwordInput).toBeDefined();
    expect(passwordInput.getAttribute('type')).toBe('password');
  });

  it('renders submit button', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    const submitButton = screen.getByTestId('login-submit');
    expect(submitButton).toBeDefined();
    expect(submitButton.textContent).toContain('Sign in');
  });

  it('updates email input on change', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    const emailInput = screen.getByTestId('login-email') as HTMLInputElement;
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });

    expect(emailInput.value).toBe('test@example.com');
  });

  it('updates password input on change', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    const passwordInput = screen.getByTestId('login-password') as HTMLInputElement;
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    expect(passwordInput.value).toBe('password123');
  });
});

describe('BookingModal Component', () => {
  const mockOnClose = vi.fn();
  const mockOnConfirm = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders when open=true', () => {
    render(
      <BookingModal
        open={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        slotLabel="Jan 1, 2025 10:00 AM"
      />
    );

    const modal = screen.getByTestId('book-modal');
    expect(modal).toBeDefined();
  });

  it('does not render when open=false', () => {
    const { container } = render(
      <BookingModal
        open={false}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        slotLabel="Test Slot"
      />
    );

    expect(container.textContent).toBe('');
  });

  it('displays slot label', () => {
    render(
      <BookingModal
        open={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        slotLabel="Jan 15, 2025 2:30 PM"
      />
    );

    const label = screen.getByTestId('book-slot-label');
    expect(label.textContent).toBe('Jan 15, 2025 2:30 PM');
  });

  it('confirm button is disabled when description is empty', () => {
    render(
      <BookingModal
        open={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        slotLabel="Test Slot"
      />
    );

    const confirmButton = screen.getByTestId('book-confirm') as HTMLButtonElement;
    expect(confirmButton.disabled).toBe(true);
  });

  it('confirm button is enabled when description has text', () => {
    render(
      <BookingModal
        open={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        slotLabel="Test Slot"
      />
    );

    const textarea = screen.getByTestId('book-description') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'Discuss project requirements' } });

    const confirmButton = screen.getByTestId('book-confirm') as HTMLButtonElement;
    expect(confirmButton.disabled).toBe(false);
  });

  it('calls onClose when close button is clicked', () => {
    render(
      <BookingModal
        open={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        slotLabel="Test Slot"
      />
    );

    const closeButton = screen.getByTestId('book-modal-close');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('calls onConfirm with description when confirm button is clicked', async () => {
    mockOnConfirm.mockResolvedValue(undefined);

    render(
      <BookingModal
        open={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        slotLabel="Test Slot"
      />
    );

    const textarea = screen.getByTestId('book-description');
    fireEvent.change(textarea, { target: { value: 'Team sync meeting' } });

    const confirmButton = screen.getByTestId('book-confirm');
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockOnConfirm).toHaveBeenCalledWith('Team sync meeting');
    });
  });

  it('shows error message when onConfirm fails', async () => {
    mockOnConfirm.mockRejectedValue(new Error('Slot already booked'));

    render(
      <BookingModal
        open={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        slotLabel="Test Slot"
      />
    );

    const textarea = screen.getByTestId('book-description');
    fireEvent.change(textarea, { target: { value: 'Meeting' } });

    const confirmButton = screen.getByTestId('book-confirm');
    fireEvent.click(confirmButton);

    await waitFor(() => {
      const error = screen.getByTestId('book-error');
      expect(error.textContent).toBe('Slot already booked');
    });
  });
});

describe('SlotList Component', () => {
  const mockSlots: Slot[] = [
    {
      id: 'slot-1',
      start_at: '2025-01-15T10:00:00Z',
      end_at: '2025-01-15T10:30:00Z',
    },
    {
      id: 'slot-2',
      start_at: '2025-01-15T14:00:00Z',
      end_at: '2025-01-15T14:30:00Z',
    },
  ];

  it('renders slot cards from props', () => {
    const mockOnBook = vi.fn();

    render(<SlotList slots={mockSlots} onBook={mockOnBook} />);

    const slotList = screen.getByTestId('slot-list');
    expect(slotList).toBeDefined();

    const slot1Card = screen.getByTestId('slot-card-slot-1');
    expect(slot1Card).toBeDefined();

    const slot2Card = screen.getByTestId('slot-card-slot-2');
    expect(slot2Card).toBeDefined();
  });

  it('renders correct number of slots', () => {
    const mockOnBook = vi.fn();

    render(<SlotList slots={mockSlots} onBook={mockOnBook} />);

    const slot1 = screen.getByTestId('slot-card-slot-1');
    const slot2 = screen.getByTestId('slot-card-slot-2');

    expect(slot1).toBeDefined();
    expect(slot2).toBeDefined();
  });

  it('shows "No available slots" when slots array is empty', () => {
    const mockOnBook = vi.fn();

    render(<SlotList slots={[]} onBook={mockOnBook} />);

    const noSlots = screen.getByTestId('no-slots');
    expect(noSlots.textContent).toContain('No available slots');
  });

  it('clicking Book button calls onBook callback with correct slot', () => {
    const mockOnBook = vi.fn();

    render(<SlotList slots={mockSlots} onBook={mockOnBook} />);

    const bookButton = screen.getByTestId('slot-book-slot-1');
    fireEvent.click(bookButton);

    expect(mockOnBook).toHaveBeenCalledTimes(1);
    expect(mockOnBook).toHaveBeenCalledWith(mockSlots[0]);
  });

  it('each slot has a Book button', () => {
    const mockOnBook = vi.fn();

    render(<SlotList slots={mockSlots} onBook={mockOnBook} />);

    mockSlots.forEach((slot) => {
      const bookButton = screen.getByTestId(`slot-book-${slot.id}`);
      expect(bookButton).toBeDefined();
      expect(bookButton.textContent).toBe('Book');
    });
  });
});

