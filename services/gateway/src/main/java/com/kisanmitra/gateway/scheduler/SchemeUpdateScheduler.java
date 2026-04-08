package com.kisanmitra.gateway.scheduler;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class SchemeUpdateScheduler {

    @Scheduled(cron = "0 0 9 * * *") // 9 AM daily
    public void notifyNewSchemes() {
        log.info("Checking for newly added schemes...");
        // TODO: Check schemes with created_at in last 24 hours
        // Match against active user profiles for eligibility
        // Send notifications to eligible users
    }
}
