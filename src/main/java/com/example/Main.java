package com.example;

/**
 * Main application class - Simple calculator demo
 */
public class Main {
    
    public static void main(String[] args) {
        printHeader();
        runCalculatorDemo();
        printFooter();
    }
    
    private static void printHeader() {
        System.out.println("Simple Calculator Application");
        System.out.println("=============================");
    }
    
    private static void runCalculatorDemo() {
        Calculator calc = new Calculator();
        
        System.out.println("\nBasic Operations:");
        System.out.println("10 + 5 = " + calc.add(10, 5));
        System.out.println("10 - 5 = " + calc.subtract(10, 5));
        System.out.println("10 * 5 = " + calc.multiply(10, 5));
        System.out.println("10 / 5 = " + calc.divide(10, 5));
        
        System.out.println("\nAdvanced Operations:");
        System.out.println("2^8 = " + calc.power(2, 8));
        System.out.println("√16 = " + calc.squareRoot(16));
        
        demonstrateErrorHandling(calc);
    }
    
    private static void demonstrateErrorHandling(Calculator calc) {
        System.out.println("\nError Handling:");
        try {
            calc.divide(10, 0);
        } catch (IllegalArgumentException e) {
            System.out.println("✓ Caught: " + e.getMessage());
        }
        
        try {
            calc.squareRoot(-4);
        } catch (IllegalArgumentException e) {
            System.out.println("✓ Caught: " + e.getMessage());
        }
    }
    
    private static void printFooter() {
        System.out.println("\n✓ All operations completed successfully!");
    }
}
