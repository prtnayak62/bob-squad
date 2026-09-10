package com.example;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link Calculator} and {@link UserService}.
 *
 * <p>Each test verifies a single behaviour and has a descriptive name
 * so failures are immediately actionable without reading the body.</p>
 */
@DisplayName("Calculator and UserService Tests")
public class UserServiceTest {

    private Calculator calculator;
    private UserService userService;

    @BeforeEach
    void setUp() {
        calculator = new Calculator();
        userService = new UserService();
    }

    // -----------------------------------------------------------------------
    // Calculator — basic operations
    // -----------------------------------------------------------------------

    @Test
    @DisplayName("add: 3 + 4 should equal 7")
    void testAdd() {
        assertEquals(7, calculator.add(3, 4));
    }

    @Test
    @DisplayName("subtract: 10 - 3 should equal 7")
    void testSubtract() {
        assertEquals(7, calculator.subtract(10, 3));
    }

    @Test
    @DisplayName("multiply: 3 * 4 should equal 12")
    void testMultiply() {
        assertEquals(12, calculator.multiply(3, 4));
    }

    @Test
    @DisplayName("divide: 10 / 2 should equal 5.0")
    void testDivide() {
        assertEquals(5.0, calculator.divide(10, 2), 0.001);
    }

    @Test
    @DisplayName("divide: dividing by zero throws ArithmeticException")
    void testDivideByZeroThrows() {
        assertThrows(ArithmeticException.class, () -> calculator.divide(10, 0));
    }

    @Test
    @DisplayName("power: 2^8 should equal 256.0")
    void testPower() {
        assertEquals(256.0, calculator.power(2, 8), 0.001);
    }

    @Test
    @DisplayName("squareRoot: sqrt(16) should equal 4.0")
    void testSquareRoot() {
        assertEquals(4.0, calculator.squareRoot(16), 0.001);
    }

    @Test
    @DisplayName("squareRoot: negative input throws ArithmeticException")
    void testSquareRootNegativeThrows() {
        assertThrows(ArithmeticException.class, () -> calculator.squareRoot(-4));
    }

    @Test
    @DisplayName("abs: abs(-5) should equal 5")
    void testAbs() {
        assertEquals(5, calculator.abs(-5));
    }

    // -----------------------------------------------------------------------
    // UserService
    // -----------------------------------------------------------------------

    @Test
    @DisplayName("UserService: new instance has zero users")
    void testNewServiceIsEmpty() {
        assertEquals(0, userService.getUserCount());
        assertTrue(userService.getAllUsers().isEmpty());
    }

    @Test
    @DisplayName("UserService: addUser increases count by 1")
    void testAddUserIncreasesCount() {
        userService.addUser("Alice");
        assertEquals(1, userService.getUserCount());
    }

    @Test
    @DisplayName("UserService: getAllUsers contains added name")
    void testGetAllUsersContainsAddedName() {
        userService.addUser("Bob");
        assertTrue(userService.getAllUsers().contains("Bob"));
    }

    @Test
    @DisplayName("UserService: addUser with blank name throws IllegalArgumentException")
    void testAddBlankUserThrows() {
        assertThrows(IllegalArgumentException.class, () -> userService.addUser("  "));
    }

    @Test
    @DisplayName("UserService: addUser with null throws IllegalArgumentException")
    void testAddNullUserThrows() {
        assertThrows(IllegalArgumentException.class, () -> userService.addUser(null));
    }

    @Test
    @DisplayName("UserService: clearUsers resets count to zero")
    void testClearUsers() {
        userService.addUser("Alice");
        userService.addUser("Bob");
        userService.clearUsers();
        assertEquals(0, userService.getUserCount());
    }
}
