package com.matketing.be.domain.notification.service;

import com.google.firebase.messaging.*;
import com.matketing.be.domain.notification.entity.DeviceToken;
import com.matketing.be.domain.notification.repository.DeviceTokenRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class FcmPushService {

    private final DeviceTokenRepository deviceTokenRepository;

    // 전달받은 디바이스 토큰 목록으로 FCM 푸시 알림을 발송하고 성공/실패 건수를 반환한다.
    @Transactional
    public int[] sendPushNotification(List<DeviceToken> deviceTokens, String title, String body, String webUrl) {
        int sentCount = 0;
        int failedCount = 0;

        if (deviceTokens.isEmpty()) {
            return new int[]{sentCount, failedCount};
        }

        for (DeviceToken deviceToken : deviceTokens) {
            try {
                Message.Builder messageBuilder = Message.builder()
                        .setToken(deviceToken.getToken())
                        .setNotification(Notification.builder()
                                .setTitle(title)
                                .setBody(body)
                                .build())
                        .putData("title", title)
                        .putData("body", body);

                if (webUrl != null && !webUrl.isEmpty()) {
                    messageBuilder.putData("web_url", webUrl);
                }

                Message message = messageBuilder.build();
                String response = FirebaseMessaging.getInstance().send(message);
                log.info("Successfully sent message: {} to token: {}", response, deviceToken.getToken());
                sentCount++;

            } catch (FirebaseMessagingException e) {
                log.error("Failed to send message to token: {}. Error: {}", deviceToken.getToken(), e.getMessage());
                handleFirebaseMessagingException(e, deviceToken);
                failedCount++;
            } catch (Exception e) {
                log.error("Unexpected error sending message to token: {}", deviceToken.getToken(), e);
                failedCount++;
            }
        }
        return new int[]{sentCount, failedCount};
    }

    private void handleFirebaseMessagingException(FirebaseMessagingException e, DeviceToken deviceToken) {
        MessagingErrorCode errorCode = e.getMessagingErrorCode();
        if (errorCode == MessagingErrorCode.UNREGISTERED ||
            errorCode == MessagingErrorCode.INVALID_ARGUMENT) {
            log.info("Token {} is invalid or unregistered. Deactivating.", deviceToken.getToken());
            deviceToken.deactivate();
        }
    }
}
