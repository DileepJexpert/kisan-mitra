package com.kisanmitra.gateway.repository;

import com.kisanmitra.gateway.model.Scheme;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface SchemeRepository extends JpaRepository<Scheme, UUID> {
    Optional<Scheme> findBySchemeCode(String schemeCode);
    List<Scheme> findBySectorAndIsActiveTrue(String sector);
    List<Scheme> findByIsActiveTrue();
}
