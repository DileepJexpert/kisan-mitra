package com.kisanmitra.gateway.repository;

import com.kisanmitra.gateway.model.SchemeApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface SchemeApplicationRepository extends JpaRepository<SchemeApplication, UUID> {
    List<SchemeApplication> findByUserId(UUID userId);
    List<SchemeApplication> findByUserIdAndStatus(UUID userId, String status);
}
