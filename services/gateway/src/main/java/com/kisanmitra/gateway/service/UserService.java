package com.kisanmitra.gateway.service;

import com.kisanmitra.gateway.dto.UpdateUserRequest;
import com.kisanmitra.gateway.dto.UserDTO;
import com.kisanmitra.gateway.model.User;
import com.kisanmitra.gateway.repository.UserRepository;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;

    public UserDTO getProfile(UUID userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        return toDTO(user);
    }

    public UserDTO updateProfile(UUID userId, UpdateUserRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new EntityNotFoundException("User not found"));

        if (request.getName() != null) user.setName(request.getName());
        if (request.getLanguage() != null) user.setLanguage(request.getLanguage());
        if (request.getState() != null) user.setState(request.getState());
        if (request.getDistrict() != null) user.setDistrict(request.getDistrict());
        if (request.getPincode() != null) user.setPincode(request.getPincode());
        if (request.getCategory() != null) user.setCategory(request.getCategory());
        if (request.getGender() != null) user.setGender(request.getGender());
        if (request.getIncomeAnnual() != null) user.setIncomeAnnual(request.getIncomeAnnual());
        if (request.getLandAcres() != null) user.setLandAcres(request.getLandAcres());
        if (request.getOccupation() != null) user.setOccupation(request.getOccupation());
        if (request.getUdyamNumber() != null) user.setUdyamNumber(request.getUdyamNumber());

        userRepository.save(user);
        return toDTO(user);
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
