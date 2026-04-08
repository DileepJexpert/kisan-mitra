package com.kisanmitra.gateway.controller;

import com.kisanmitra.gateway.dto.UpdateUserRequest;
import com.kisanmitra.gateway.dto.UserDTO;
import com.kisanmitra.gateway.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/me")
    public ResponseEntity<UserDTO> getProfile(Authentication auth) {
        UUID userId = UUID.fromString(auth.getName());
        return ResponseEntity.ok(userService.getProfile(userId));
    }

    @PutMapping("/me")
    public ResponseEntity<UserDTO> updateProfile(Authentication auth,
                                                   @RequestBody UpdateUserRequest request) {
        UUID userId = UUID.fromString(auth.getName());
        return ResponseEntity.ok(userService.updateProfile(userId, request));
    }
}
