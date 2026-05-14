package com.matketing.be.domain.content.client;

import com.matketing.be.domain.content.config.ContentS3Properties;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import software.amazon.awssdk.awscore.exception.AwsServiceException;
import software.amazon.awssdk.core.exception.SdkClientException;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.model.S3Exception;

@Slf4j
@Component
@RequiredArgsConstructor
public class S3VideoClient {

    private final S3Client s3Client;
    private final ContentS3Properties properties;

    public String uploadVideo(String objectKey, MultipartFile videoFile) {
        if (properties.bucketName() == null || properties.bucketName().isBlank()) {
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        String normalizedKey = normalizeKey(objectKey);

        try {
            PutObjectRequest request = PutObjectRequest.builder()
                    .bucket(properties.bucketName())
                    .key(normalizedKey)
                    .contentType(videoFile.getContentType())
                    .contentLength(videoFile.getSize())
                    .build();
            
            s3Client.putObject(request, RequestBody.fromInputStream(videoFile.getInputStream(), videoFile.getSize()));
            
            log.info("[VideoUpload] S3 upload completed. bucket={}, key={}", properties.bucketName(), normalizedKey);
            return objectKey;
        } catch (S3Exception exception) {
            log.error("[VideoUpload] S3 upload failed. bucket={}, key={}, region={}, fileSize={}, contentType={}, exceptionClass={}, statusCode={}, errorCode={}, message={}",
                    properties.bucketName(), normalizedKey, properties.region(), videoFile.getSize(), videoFile.getContentType(),
                    exception.getClass().getSimpleName(), exception.statusCode(), exception.awsErrorDetails().errorCode(), exception.getMessage());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR, exception);
        } catch (AwsServiceException exception) {
            log.error("[VideoUpload] S3 upload failed (AwsServiceException). bucket={}, key={}, region={}, fileSize={}, contentType={}, exceptionClass={}, statusCode={}, errorCode={}, message={}",
                    properties.bucketName(), normalizedKey, properties.region(), videoFile.getSize(), videoFile.getContentType(),
                    exception.getClass().getSimpleName(), exception.statusCode(), exception.awsErrorDetails().errorCode(), exception.getMessage());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR, exception);
        } catch (SdkClientException exception) {
            log.error("[VideoUpload] S3 upload failed (SdkClientException). bucket={}, key={}, region={}, fileSize={}, contentType={}, exceptionClass={}, message={}",
                    properties.bucketName(), normalizedKey, properties.region(), videoFile.getSize(), videoFile.getContentType(),
                    exception.getClass().getSimpleName(), exception.getMessage());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR, exception);
        } catch (Exception exception) {
            log.error("[VideoUpload] S3 upload failed (General Exception). bucket={}, key={}, region={}, fileSize={}, contentType={}, exceptionClass={}, message={}",
                    properties.bucketName(), normalizedKey, properties.region(), videoFile.getSize(), videoFile.getContentType(),
                    exception.getClass().getSimpleName(), exception.getMessage(), exception);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR, exception);
        }
    }

    private String normalizeKey(String objectKey) {
        return objectKey.startsWith("/") ? objectKey.substring(1) : objectKey;
    }
}
