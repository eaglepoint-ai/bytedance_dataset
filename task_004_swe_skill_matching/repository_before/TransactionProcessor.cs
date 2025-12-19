using System;
using System.Collections.Generic;
using System.Linq;

namespace repository_before
{
    public enum AccountType
    {
        Standard,
        Premium,
        Business
    }

    public enum TransactionType
    {
        Domestic,
        International,
        Instant
    }

    public enum Channel
    {
        Branch,
        MobileApp,
        Web,
        ATM
    }

    public class TransactionRequest
    {
        public decimal Amount { get; set; }
        public TransactionType TransactionType { get; set; }
        public Channel Channel { get; set; }
        public string Location { get; set; } = string.Empty;
        public string Currency { get; set; } = "USD";
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }

    public class CustomerProfile
    {
        public int Id { get; set; }
        public AccountType AccountType { get; set; }
        public decimal DailyLimit { get; set; } = 10000m;
        public bool HasOverdraftProtection { get; set; }
        public decimal OverdraftLimit { get; set; } = 500m;
        public decimal AverageTransaction { get; set; } = 250m;
        public string HomeLocation { get; set; } = "UNKNOWN";
        public string LastLoginLocation { get; set; } = "UNKNOWN";
        public int MonthlyTransactionCount { get; set; }
        public decimal LoyaltyScore { get; set; }
        public List<string> FrequentTravelLocations { get; set; } = new List<string>();
    }

    public class TransactionResult
    {
        public decimal ProcessedAmount { get; set; }
        public bool RequiresReview { get; set; }
        public string ReferenceNumber { get; set; } = string.Empty;
        public List<string> Messages { get; } = new List<string>();

        public void AddMessage(string message)
        {
            if (!string.IsNullOrWhiteSpace(message))
            {
                Messages.Add(message.Trim());
            }
        }
    }

    public class DailyLimitExceededException : Exception
    {
        public DailyLimitExceededException()
            : base("The customer has exceeded the configured daily transfer limit.")
        {
        }
    }

    public class NightTimeLimitException : Exception
    {
        public NightTimeLimitException()
            : base("Transactions over the allowed threshold cannot be processed at night.")
        {
        }
    }

    public class TransactionProcessor
    {
        private static readonly Dictionary<string, decimal> CurrencyAdjustmentFactors =
            new(StringComparer.OrdinalIgnoreCase)
            {
                ["USD"] = 1.0m,
                ["EUR"] = 1.02m,
                ["GBP"] = 1.01m,
                ["JPY"] = 0.007m
            };

        private readonly Dictionary<(int CustomerId, DateTime Date), decimal> _dailyTotals =
            new();

        private readonly object _syncRoot = new();

        public TransactionResult ProcessTransaction(TransactionRequest request, CustomerProfile customer)
        {
            if (request == null)
            {
                throw new ArgumentNullException(nameof(request));
            }

            if (customer == null)
            {
                throw new ArgumentNullException(nameof(customer));
            }

            if (request.Amount <= 0)
            {
                throw new ArgumentException("Transaction amount must be positive.", nameof(request));
            }

            var result = new TransactionResult();
            decimal finalAmount = request.Amount;

            if (customer.AccountType == AccountType.Premium)
            {
                if (request.TransactionType == TransactionType.International)
                {
                    finalAmount += CalculateInternationalFee(request, customer);
                }
                else if (request.Channel == Channel.MobileApp)
                {
                    finalAmount -= Math.Round(finalAmount * 0.001m, 2, MidpointRounding.AwayFromZero);
                    result.AddMessage("Premium mobile discount applied.");
                }
            }
            else if (customer.AccountType == AccountType.Business)
            {
                if (customer.MonthlyTransactionCount < 100)
                {
                    finalAmount += 2.50m;
                    result.AddMessage("Business low-volume fee applied.");
                }
            }

            var today = request.Timestamp.Date;
            var dailyTotal = GetDailyTotal(customer.Id, today);
            if (dailyTotal + finalAmount > customer.DailyLimit)
            {
                if (customer.HasOverdraftProtection && request.Amount <= customer.OverdraftLimit)
                {
                    finalAmount += 25.00m;
                    result.AddMessage("Overdraft processing fee added.");
                }
                else
                {
                    throw new DailyLimitExceededException();
                }
            }

            bool isSuspicious = false;
            if (request.Amount > 10000m && customer.AverageTransaction < 1000m)
            {
                isSuspicious = true;
                result.AddMessage("High-value transaction flagged for review.");
            }

            if (!string.Equals(request.Location, customer.HomeLocation, StringComparison.OrdinalIgnoreCase) &&
                string.Equals(customer.LastLoginLocation, request.Location, StringComparison.OrdinalIgnoreCase))
            {
                if (!IsExpectedTravel(customer, request.Location))
                {
                    isSuspicious = true;
                    result.AddMessage("Unexpected travel pattern detected.");
                }
            }

            var utcNow = DateTime.UtcNow;
            if (utcNow.Hour >= 20 || utcNow.Hour < 6)
            {
                finalAmount += 1.00m;
                if (request.Amount > 5000m)
                {
                    throw new NightTimeLimitException();
                }
            }

            if (utcNow.DayOfWeek is DayOfWeek.Saturday or DayOfWeek.Sunday)
            {
                if (request.TransactionType == TransactionType.Instant)
                {
                    var weekendFee = Math.Round(finalAmount * 0.015m, 2, MidpointRounding.AwayFromZero);
                    finalAmount += weekendFee;
                    result.AddMessage("Weekend instant processing fee applied.");
                }
            }

            UpdateDailyTotal(customer.Id, today, finalAmount);

            result.ProcessedAmount = decimal.Round(finalAmount, 2, MidpointRounding.AwayFromZero);
            result.RequiresReview = isSuspicious;
            result.ReferenceNumber = GenerateReferenceNumber();
            return result;
        }

        private decimal CalculateInternationalFee(TransactionRequest request, CustomerProfile customer)
        {
            var adjustmentFactor = CurrencyAdjustmentFactors.TryGetValue(request.Currency, out var factor)
                ? factor
                : 1.05m;

            var fxFee = request.Amount * 0.005m * adjustmentFactor;
            var networkFee = request.Channel == Channel.MobileApp ? 0.50m : 1.00m;

            if (customer.LoyaltyScore >= 80)
            {
                fxFee *= 0.85m;
            }

            return decimal.Round(fxFee + networkFee, 2, MidpointRounding.AwayFromZero);
        }

        private bool IsExpectedTravel(CustomerProfile customer, string location)
        {
            if (string.IsNullOrWhiteSpace(location))
            {
                return true;
            }

            if (string.Equals(location, customer.HomeLocation, StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }

            return customer.FrequentTravelLocations.Any(l =>
                string.Equals(l, location, StringComparison.OrdinalIgnoreCase));
        }

        private string GenerateReferenceNumber()
        {
            return $"TX-{DateTime.UtcNow:yyyyMMddHHmmss}-{Guid.NewGuid():N}"
                .ToUpperInvariant();
        }

        private decimal GetDailyTotal(int customerId, DateTime date)
        {
            lock (_syncRoot)
            {
                return _dailyTotals.TryGetValue((customerId, date), out var amount) ? amount : 0m;
            }
        }

        private void UpdateDailyTotal(int customerId, DateTime date, decimal processedAmount)
        {
            lock (_syncRoot)
            {
                var key = (customerId, date);
                if (_dailyTotals.TryGetValue(key, out var currentTotal))
                {
                    _dailyTotals[key] = currentTotal + processedAmount;
                }
                else
                {
                    _dailyTotals[key] = processedAmount;
                }
            }
        }
    }
}
