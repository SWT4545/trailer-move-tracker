"""
Payment Processing Module
Handles factoring fees, service fees, and driver payment calculations
"""

class PaymentProcessor:
    FACTORING_FEE_RATE = 0.03  # 3% factoring fee
    BASE_RATE_PER_MILE = 2.10  # $2.10 per mile
    
    @staticmethod
    def calculate_initial_estimate(total_earnings, num_drivers=1):
        """
        Calculate initial payment estimate using 3% factoring fee
        
        Args:
            total_earnings: Total amount before any fees
            num_drivers: Number of drivers splitting the payment
            
        Returns:
            dict with calculation breakdown
        """
        factoring_fee = total_earnings * PaymentProcessor.FACTORING_FEE_RATE
        estimated_gross_net = total_earnings - factoring_fee
        estimated_net_per_driver = estimated_gross_net / num_drivers
        
        return {
            'total_earnings': total_earnings,
            'factoring_fee': factoring_fee,
            'factoring_fee_rate': PaymentProcessor.FACTORING_FEE_RATE,
            'estimated_gross_net': estimated_gross_net,
            'num_drivers': num_drivers,
            'estimated_net_per_driver': estimated_net_per_driver
        }
    
    @staticmethod
    def calculate_final_payment(total_earnings, service_fee, num_drivers=1):
        """
        Calculate final payment after receiving actual service fee from factoring company
        
        Args:
            total_earnings: Total amount before any fees
            service_fee: Actual service fee from factoring company
            num_drivers: Number of drivers splitting the payment
            
        Returns:
            dict with complete payment breakdown
        """
        factoring_fee = total_earnings * PaymentProcessor.FACTORING_FEE_RATE
        total_fees = factoring_fee + service_fee
        final_gross_net = total_earnings - total_fees
        service_fee_per_driver = service_fee / num_drivers
        final_net_per_driver = (final_gross_net / num_drivers)
        
        return {
            'total_earnings': total_earnings,
            'factoring_fee': factoring_fee,
            'service_fee': service_fee,
            'total_fees': total_fees,
            'final_gross_net': final_gross_net,
            'num_drivers': num_drivers,
            'service_fee_per_driver': service_fee_per_driver,
            'final_net_per_driver': final_net_per_driver
        }
    
    @staticmethod
    def calculate_miles_from_pay(driver_pay_after_fees):
        """
        Calculate miles based on driver's net pay (after all fees)
        
        Args:
            driver_pay_after_fees: Driver's net payment after factoring and service fees
            
        Returns:
            Estimated miles traveled
        """
        # Since driver gets $2.10 per mile BEFORE fees
        # We need to work backwards from their net pay
        # This is an approximation since we don't know the exact fee structure
        # For exact miles, we should store them directly
        
        # Rough estimate: add back approximately 3% for factoring + service fee
        estimated_gross = driver_pay_after_fees / 0.97
        miles = estimated_gross / PaymentProcessor.BASE_RATE_PER_MILE
        return round(miles, 1)
    
    @staticmethod
    def calculate_gross_from_net(net_pay, service_fee=6.00):
        """
        Calculate gross earnings from net pay (reverse calculation)
        
        Args:
            net_pay: Net payment after all fees
            service_fee: Service fee amount
            
        Returns:
            Estimated gross earnings before fees
        """
        # Net = Gross - (Gross * 0.03) - service_fee
        # Net = Gross * 0.97 - service_fee
        # Net + service_fee = Gross * 0.97
        # Gross = (Net + service_fee) / 0.97
        
        gross = (net_pay + service_fee) / (1 - PaymentProcessor.FACTORING_FEE_RATE)
        return round(gross, 2)
    
    @staticmethod
    def format_payment_breakdown(payment_data):
        """
        Format payment data for display
        
        Args:
            payment_data: Dictionary from calculate_initial_estimate or calculate_final_payment
            
        Returns:
            Formatted string for display
        """
        lines = []
        lines.append("=" * 50)
        lines.append("PAYMENT BREAKDOWN")
        lines.append("=" * 50)
        lines.append(f"Total Earnings: ${payment_data['total_earnings']:,.2f}")
        lines.append(f"Factoring Fee (3%): ${payment_data['factoring_fee']:,.2f}")
        
        if 'service_fee' in payment_data:
            lines.append(f"Service Fee: ${payment_data['service_fee']:,.2f}")
            lines.append(f"Total Fees: ${payment_data['total_fees']:,.2f}")
            lines.append(f"Final Gross Net: ${payment_data['final_gross_net']:,.2f}")
            
            if payment_data['num_drivers'] > 1:
                lines.append(f"\nNumber of Drivers: {payment_data['num_drivers']}")
                lines.append(f"Service Fee per Driver: ${payment_data['service_fee_per_driver']:,.2f}")
            
            lines.append(f"\nFinal Net per Driver: ${payment_data['final_net_per_driver']:,.2f}")
        else:
            lines.append(f"Estimated Gross Net: ${payment_data['estimated_gross_net']:,.2f}")
            
            if payment_data['num_drivers'] > 1:
                lines.append(f"Number of Drivers: {payment_data['num_drivers']}")
            
            lines.append(f"Estimated Net per Driver: ${payment_data['estimated_net_per_driver']:,.2f}")
        
        lines.append("=" * 50)
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    processor = PaymentProcessor()
    
    # Test with your example data
    print("EXAMPLE FROM YOUR DATA:")
    print("-" * 50)
    
    total = 6693.00
    service_fee = 6.00
    num_drivers = 3
    
    # Initial estimate
    initial = processor.calculate_initial_estimate(total, num_drivers)
    print("\nInitial Estimate (3% factoring only):")
    print(processor.format_payment_breakdown(initial))
    
    # Final calculation with actual service fee
    final = processor.calculate_final_payment(total, service_fee, num_drivers)
    print("\nFinal Payment (with actual service fee):")
    print(processor.format_payment_breakdown(final))
    
    # Calculate miles from payment
    print("\nMileage Calculation:")
    print(f"If a driver received ${final['final_net_per_driver']:,.2f} after fees,")
    miles = processor.calculate_miles_from_pay(final['final_net_per_driver'])
    print(f"they likely drove approximately {miles} miles")
    print(f"(at ${processor.BASE_RATE_PER_MILE}/mile before fees)")