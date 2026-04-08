package com.kisanmitra.gateway.scheduler;

import com.kisanmitra.gateway.model.SchemeApplication;
import com.kisanmitra.gateway.repository.SchemeApplicationRepository;
import com.kisanmitra.gateway.service.NotificationService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
@RequiredArgsConstructor
@Slf4j
public class DeadlineReminderScheduler {

    private final SchemeApplicationRepository applicationRepository;
    private final NotificationService notificationService;

    @Scheduled(cron = "0 0 8 * * *") // 8 AM daily
    public void sendDeadlineReminders() {
        log.info("Checking for upcoming scheme application deadlines...");
        LocalDateTime threeDaysFromNow = LocalDateTime.now().plusDays(3);

        applicationRepository.findAll().stream()
                .filter(app -> app.getNextDeadline() != null
                        && app.getNextDeadline().isBefore(threeDaysFromNow)
                        && app.getNextDeadline().isAfter(LocalDateTime.now())
                        && !"approved".equals(app.getStatus())
                        && !"rejected".equals(app.getStatus()))
                .forEach(app -> {
                    notificationService.scheduleNotification(
                            app.getUserId(),
                            "deadline_reminder",
                            "Aapki scheme application ki deadline nazdeek aa rahi hai!",
                            "whatsapp",
                            LocalDateTime.now());
                    log.info("Deadline reminder sent for application {}", app.getId());
                });
    }
}
