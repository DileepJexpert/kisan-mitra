package com.kisanmitra.gateway.service;

import com.kisanmitra.gateway.model.ScheduledNotification;
import com.kisanmitra.gateway.repository.NotificationRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class NotificationService {

    private final NotificationRepository notificationRepository;

    public ScheduledNotification scheduleNotification(UUID userId, String type,
                                                       String message, String channel,
                                                       LocalDateTime scheduledAt) {
        ScheduledNotification notification = ScheduledNotification.builder()
                .userId(userId)
                .notificationType(type)
                .messageTemplate(message)
                .channel(channel)
                .scheduledAt(scheduledAt)
                .build();
        return notificationRepository.save(notification);
    }

    @Scheduled(fixedRate = 60000) // every minute
    public void processPendingNotifications() {
        List<ScheduledNotification> pending = notificationRepository
                .findByStatusAndScheduledAtBefore("pending", LocalDateTime.now());

        for (ScheduledNotification notification : pending) {
            try {
                // In production, send via WhatsApp/SMS based on channel
                log.info("Sending notification {} to user {} via {}",
                        notification.getId(), notification.getUserId(), notification.getChannel());

                notification.setStatus("sent");
                notification.setSentAt(LocalDateTime.now());
                notificationRepository.save(notification);
            } catch (Exception e) {
                log.error("Failed to send notification {}: {}",
                        notification.getId(), e.getMessage());
                notification.setRetryCount(notification.getRetryCount() + 1);
                if (notification.getRetryCount() >= 3) {
                    notification.setStatus("failed");
                }
                notificationRepository.save(notification);
            }
        }
    }

    public void cancelNotification(UUID notificationId) {
        notificationRepository.findById(notificationId).ifPresent(notification -> {
            notification.setStatus("cancelled");
            notificationRepository.save(notification);
        });
    }
}
