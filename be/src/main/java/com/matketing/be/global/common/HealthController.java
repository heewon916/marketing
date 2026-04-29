package com.matketing.be.global.common;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class HealthController {

    @GetMapping("/health")
    public ResponseEntity<String> healthCheck() {
        return ResponseEntity.ok("BE Server is Running");
    }

    @GetMapping("/ai-health")
    public ResponseEntity<Stringbe> aiHealthCheck() {
        return ResponseEntity.ok("AI Server connection is OK");
    }
}