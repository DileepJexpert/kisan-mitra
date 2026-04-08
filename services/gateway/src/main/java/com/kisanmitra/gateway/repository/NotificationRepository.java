package com.kisanmitra.gateway.repository;

import com.kisanmitra.gateway.model.ScheduledNotification;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface NotificationRepository extends JpaRepository<ScheduledNotification, UUID> {
    List<ScheduledNotification> findByStatusAndScheduledAtBefore(String status, LocalDateTime time);
    List<ScheduledNotification> findByUserId(UUID userId);
    List<ScheduledNotification> findByUserIdAndStatus(UUID userId, String status);
}
