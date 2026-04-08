package com.kisanmitra.gateway.config;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.core.RedisTemplate;

import java.util.concurrent.TimeUnit;

/**
 * Simple Redis-based rate limiter.
 * Allows a maximum of 100 requests per minute per user.
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class RateLimitConfig {

    private final RedisTemplate<String, Object> redisTemplate;

    private static final String RATE_LIMIT_PREFIX = "rate_limit:";
    private static final int MAX_REQUESTS_PER_MINUTE = 100;
    private static final long WINDOW_SECONDS = 60;

    /**
     * Checks whether the given user is within the rate limit.
     *
     * @param userId the unique identifier of the user
     * @return true if the request is allowed (under limit), false if rate-limited
     */
    public boolean checkRateLimit(String userId) {
        String key = RATE_LIMIT_PREFIX + userId;

        try {
            Long currentCount = redisTemplate.opsForValue().increment(key);

            if (currentCount == null) {
                return false;
            }

            if (currentCount == 1L) {
                redisTemplate.expire(key, WINDOW_SECONDS, TimeUnit.SECONDS);
            }

            if (currentCount > MAX_REQUESTS_PER_MINUTE) {
                log.warn("Rate limit exceeded for user: {} (count: {})", userId, currentCount);
                return false;
            }

            return true;
        } catch (Exception e) {
            log.error("Rate limit check failed for user: {}. Allowing request. Error: {}",
                    userId, e.getMessage());
            // Fail open: allow the request if Redis is unavailable
            return true;
        }
    }
}
