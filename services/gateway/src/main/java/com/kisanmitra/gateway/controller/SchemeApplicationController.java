package com.kisanmitra.gateway.controller;

import com.kisanmitra.gateway.model.SchemeApplication;
import com.kisanmitra.gateway.repository.SchemeApplicationRepository;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/applications")
@RequiredArgsConstructor
public class SchemeApplicationController {

    private final SchemeApplicationRepository repository;

    @GetMapping
    public ResponseEntity<List<SchemeApplication>> listApplications(Authentication auth) {
        UUID userId = UUID.fromString(auth.getName());
        return ResponseEntity.ok(repository.findByUserId(userId));
    }

    @PutMapping("/{id}/status")
    public ResponseEntity<SchemeApplication> updateStatus(
            @PathVariable UUID id,
            @RequestBody Map<String, String> body) {
        SchemeApplication app = repository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Application not found"));

        app.setStatus(body.get("status"));
        if (body.containsKey("notes")) app.setNotes(body.get("notes"));
        if ("applied".equals(body.get("status"))) app.setAppliedAt(LocalDateTime.now());

        return ResponseEntity.ok(repository.save(app));
    }
}
