package com.kisanmitra.gateway.service;

import com.kisanmitra.gateway.dto.AuthResponse;
import com.kisanmitra.gateway.dto.UserDTO;
import com.kisanmitra.gateway.model.User;
import com.kisanmitra.gateway.repository.UserRepository;
import com.kisanmitra.gateway.util.JwtUtil;
import com.kisanmitra.gateway.util.OTPUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {

    private final UserRepository userRepository;
    private final RedisTemplate<String, Object> redisTemplate;
    private final JwtUtil jwtUtil;
    private final OTPUtil otpUtil;

    public String sendOtp(String phone) {
        String otp = otpUtil.generateOtp();
        String key = "otp:" + phone;
        redisTemplate.opsForValue().set(key, otp, Duration.ofMinutes(5));
        log.info("OTP generated for phone {}: {} (DEV MODE — in production, send via MSG91)", phone, otp);
        return "OTP sent successfully";
    }

    public AuthResponse verifyOtp(String phone, String otp) {
        String key = "otp:" + phone;
        Object storedOtp = redisTemplate.opsForValue().get(key);

        if (storedOtp == null || !storedOtp.toString().equals(otp)) {
            throw new IllegalArgumentException("Invalid or expired OTP");
        }

        redisTemplate.delete(key);

        User user = userRepository.findByPhone(phone).orElseGet(() -> {
            User newUser = User.builder()
                    .phone(phone)
                    .language("hi")
                    .onboardedAt(LocalDateTime.now())
                    .build();
            return userRepository.save(newUser);
        });

        user.setLastActiveAt(LocalDateTime.now());
        userRepository.save(user);

        String token = jwtUtil.generateToken(user.getId(), user.getPhone());
        String refreshToken = jwtUtil.generateRefreshToken(user.getId());

        return AuthResponse.builder()
                .token(token)
                .refreshToken(refreshToken)
                .user(toDTO(user))
                .build();
    }

    public AuthResponse refreshToken(String refreshToken) {
        if (!jwtUtil.validateToken(refreshToken)) {
            throw new IllegalArgumentException("Invalid refresh token");
        }
        var userId = jwtUtil.extractUserId(refreshToken);
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found"));

        String newToken = jwtUtil.generateToken(user.getId(), user.getPhone());
        String newRefreshToken = jwtUtil.generateRefreshToken(user.getId());

        return AuthResponse.builder()
                .token(newToken)
                .refreshToken(newRefreshToken)
                .user(toDTO(user))
                .build();
    }

    private UserDTO toDTO(User user) {
        return UserDTO.builder()
                .id(user.getId())
                .phone(user.getPhone())
                .name(user.getName())
                .language(user.getLanguage())
                .state(user.getState())
                .district(user.getDistrict())
                .occupation(user.getOccupation())
                .subscriptionTier(user.getSubscriptionTier())
                .build();
    }
}
