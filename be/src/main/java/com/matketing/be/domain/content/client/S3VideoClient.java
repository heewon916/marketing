package com.matketing.be.domain.content.client;

import com.matketing.be.domain.content.config.ContentS3Properties;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

@Component
@RequiredArgsConstructor
public class S3VideoClient {

    private final S3Client s3Client;
    private final ContentS3Properties properties;

    public String uploadVideo(String objectKey, MultipartFile videoFile) {
        if (properties.bucketName() == null || properties.bucketName().isBlank()) {
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        try {
            PutObjectRequest request = PutObjectRequest.builder()
                    .bucket(properties.bucketName())
                    .key(normalizeKey(objectKey))
                    .contentType(videoFile.getContentType())
                    .contentLength(videoFile.getSize())
                    .build();
            s3Client.putObject(request, RequestBody.fromInputStream(videoFile.getInputStream(), videoFile.getSize()));
            return objectKey;
        } catch (Exception exception) {
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR, exception);
        }
    }

    private String normalizeKey(String objectKey) {
        return objectKey.startsWith("/") ? objectKey.substring(1) : objectKey;
    }
}
