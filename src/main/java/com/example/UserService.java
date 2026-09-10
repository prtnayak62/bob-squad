package com.example;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.logging.Logger;

/**
 * UserService manages a simple in-memory collection of user names.
 *
 * <p>This class is intentionally kept simple to serve as a demonstration
 * target for the Claude AI code review pipeline.</p>
 *
 * @author Demo Project
 * @version 1.0
 */
public class UserService {

    private static final Logger LOGGER = Logger.getLogger(UserService.class.getName());

    private final List<String> users;

    /** Creates a new UserService with an empty user list. */
    public UserService() {
        this.users = new ArrayList<>();
    }

    /**
     * Returns an unmodifiable view of all users.
     *
     * @return unmodifiable list of user names; never {@code null}
     */
    public List<String> getAllUsers() {
        LOGGER.fine("getAllUsers called, returning " + users.size() + " users");
        return Collections.unmodifiableList(users);
    }

    /**
     * Adds a user to the service.
     *
     * @param name the user name — must not be null or blank
     * @throws IllegalArgumentException if {@code name} is null or blank
     */
    public void addUser(String name) {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("User name must not be null or blank");
        }
        users.add(name.trim());
        LOGGER.info("Added user: " + name.trim());
    }

    /**
     * Returns the number of users currently managed by this service.
     *
     * @return the user count — always &gt;= 0
     */
    public int getUserCount() {
        return users.size();
    }

    /**
     * Removes all users from the service.
     */
    public void clearUsers() {
        LOGGER.info("Clearing all " + users.size() + " users");
        users.clear();
    }
}
