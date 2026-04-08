package com.kisanmitra.gateway.util;

import org.springframework.stereotype.Component;

import java.security.SecureRandom;

@Component
public class OTPUtil {

    private static final SecureRandom SECURE_RANDOM = new SecureRandom();
    private static final int OTP_LENGTH = 6;
    private static final int OTP_BOUND = 1_000_000;

    /**
     * Generates a cryptographically secure random 6-digit OTP.
     *
     * @return a zero-padded 6-digit string (e.g., "003821")
     */
    public String generateOtp() {
        int otp = SECURE_RANDOM.nextInt(OTP_BOUND);
        return String.format("%0" + OTP_LENGTH + "d", otp);
    }
}
