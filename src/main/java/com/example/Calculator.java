package com.example;

import java.util.logging.Logger;

/**
 * Calculator provides basic and advanced arithmetic operations.
 *
 * <p>All methods are stateless and thread-safe. Input validation is
 * performed on every operation to prevent undefined behaviour.</p>
 *
 * @author Demo Project
 * @version 2.0
 */
public class Calculator {

    private static final Logger LOGGER = Logger.getLogger(Calculator.class.getName());

    /**
     * Adds two integers.
     *
     * @param a first operand
     * @param b second operand
     * @return the sum {@code a + b}
     */
    public int add(int a, int b) {
        int result = a + b;
        LOGGER.fine(() -> String.format("add(%d, %d) = %d", a, b, result));
        return result;
    }

    /**
     * Subtracts {@code b} from {@code a}.
     *
     * @param a minuend
     * @param b subtrahend
     * @return the difference {@code a - b}
     */
    public int subtract(int a, int b) {
        int result = a - b;
        LOGGER.fine(() -> String.format("subtract(%d, %d) = %d", a, b, result));
        return result;
    }

    /**
     * Multiplies two integers.
     *
     * @param a first factor
     * @param b second factor
     * @return the product {@code a * b}
     */
    public int multiply(int a, int b) {
        int result = a * b;
        LOGGER.fine(() -> String.format("multiply(%d, %d) = %d", a, b, result));
        return result;
    }

    /**
     * Divides {@code a} by {@code b}.
     *
     * @param a dividend
     * @param b divisor — must not be zero
     * @return the quotient {@code a / b} as a double
     * @throws ArithmeticException if {@code b} is zero
     */
    public double divide(int a, int b) {
        if (b == 0) {
            throw new ArithmeticException("Division by zero is not allowed");
        }
        double result = (double) a / b;
        LOGGER.fine(() -> String.format("divide(%d, %d) = %f", a, b, result));
        return result;
    }

    /**
     * Raises {@code base} to the power of {@code exponent}.
     *
     * @param base     the base value
     * @param exponent the exponent (may be negative)
     * @return {@code base} raised to {@code exponent}
     */
    public double power(double base, int exponent) {
        double result = Math.pow(base, exponent);
        LOGGER.fine(() -> String.format("power(%f, %d) = %f", base, exponent, result));
        return result;
    }

    /**
     * Calculates the square root of {@code number}.
     *
     * @param number the value — must be non-negative
     * @return the non-negative square root of {@code number}
     * @throws ArithmeticException if {@code number} is negative
     */
    public double squareRoot(double number) {
        if (number < 0) {
            throw new ArithmeticException(
                    "Square root of a negative number is undefined in real numbers");
        }
        double result = Math.sqrt(number);
        LOGGER.fine(() -> String.format("squareRoot(%f) = %f", number, result));
        return result;
    }

    /**
     * Calculates the absolute value of {@code number}.
     *
     * @param number any integer
     * @return the absolute value of {@code number}
     */
    public int abs(int number) {
        return Math.abs(number);
    }
}
