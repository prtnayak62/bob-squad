package com.example;

/**
 * Simple Calculator class demonstrating clean code practices
 * No external dependencies, easy to test and maintain
 */
public class Calculator {
    
    /**
     * Adds two numbers
     * @param a First number
     * @param b Second number
     * @return Sum of a and b
     */
    public int add(int a, int b) {
        return a + b;
    }
    
    /**
     * Subtracts second number from first
     * @param a First number
     * @param b Second number
     * @return Difference of a and b
     */
    public int subtract(int a, int b) {
        return a - b;
    }
    
    /**
     * Multiplies two numbers
     * @param a First number
     * @param b Second number
     * @return Product of a and b
     */
    public int multiply(int a, int b) {
        return a * b;
    }
    
    /**
     * Divides first number by second
     * @param a Dividend
     * @param b Divisor
     * @return Quotient of a divided by b
     * @throws IllegalArgumentException if divisor is zero
     */
    public double divide(int a, int b) {
        if (b == 0) {
            throw new IllegalArgumentException("Cannot divide by zero");
        }
        return (double) a / b;
    }
    
    /**
     * Calculates power of a number
     * @param base Base number
     * @param exponent Exponent
     * @return base raised to the power of exponent
     */
    public double power(double base, int exponent) {
        return Math.pow(base, exponent);
    }
    
    /**
     * Calculates square root
     * @param number Number to find square root of
     * @return Square root of the number
     * @throws IllegalArgumentException if number is negative
     */
    public double squareRoot(double number) {
        if (number < 0) {
            throw new IllegalArgumentException("Cannot calculate square root of negative number");
        }
        return Math.sqrt(number);
    }
}