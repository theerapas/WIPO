from mpmath import mp
import sympy

# Set precision
mp.dps = 1000  # Decimal places

# Get e as a string
e_str = str(mp.e).replace(".", "")  # Remove the decimal point

print(e_str)

# Slide through the digits to find a 10-digit prime
for i in range(len(e_str) - 9):
    ten_digits = int(e_str[i : i + 10])
    if sympy.isprime(ten_digits):
        print("First 10-digit prime in digits of e:", ten_digits)
        print("At position:", i, "-", i + 10)
        break
