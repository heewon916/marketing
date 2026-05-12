package com.matketing.be.domain.content.client;

import com.matketing.be.domain.content.config.ClovaSttProperties;
import com.matketing.be.global.exception.BusinessException;
import com.matketing.be.global.exception.ErrorCode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@Component
@RequiredArgsConstructor
public class ClovaSttAudioConverter {

    private final ClovaSttProperties properties;

    public byte[] toSupportedAudioBytes(MultipartFile audioFile) throws IOException {
        byte[] sourceBytes = audioFile.getBytes();
        if (!requiresTranscoding(audioFile)) {
            return sourceBytes;
        }

        return transcodeToWav(sourceBytes, extension(audioFile));
    }

    private boolean requiresTranscoding(MultipartFile audioFile) {
        String contentType = audioFile.getContentType();
        if (contentType != null) {
            String normalized = contentType.toLowerCase(Locale.ROOT);
            if (normalized.contains("webm") || normalized.contains("mp4") || normalized.contains("m4a")) {
                return true;
            }
        }

        String extension = extension(audioFile);
        return extension.equals("webm") || extension.equals("m4a") || extension.equals("mp4");
    }

    private String extension(MultipartFile audioFile) {
        String filename = audioFile.getOriginalFilename();
        if (filename == null) {
            return "audio";
        }
        int dotIndex = filename.lastIndexOf('.');
        if (dotIndex < 0 || dotIndex == filename.length() - 1) {
            return "audio";
        }
        return filename.substring(dotIndex + 1).toLowerCase(Locale.ROOT);
    }

    private byte[] transcodeToWav(byte[] sourceBytes, String sourceExtension) {
        String suffix = "." + sourceExtension.replaceAll("[^a-z0-9]", "");
        if (suffix.length() == 1) {
            suffix = ".audio";
        }
        Path input = null;
        Path output = null;
        try {
            input = Files.createTempFile("clova-stt-", suffix);
            output = Files.createTempFile("clova-stt-", ".wav");
            Files.write(input, sourceBytes);

            // 프론트/모바일 녹음 파일(webm, m4a, mp4)은 단문 STT 전처리에서 실패할 수 있다.
            // CLOVA Speech 단문 API가 안정적으로 처리하는 WAV로 변환해서 application/octet-stream으로 전송한다.
            Process process = new ProcessBuilder(
                    properties.ffmpegPath(),
                    "-y",
                    "-hide_banner",
                    "-loglevel", "error",
                    "-i", input.toString(),
                    "-ac", "1",
                    "-ar", "16000",
                    "-f", "wav",
                    output.toString()
            ).redirectErrorStream(true).start();

            String ffmpegOutput = new String(process.getInputStream().readAllBytes());
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                log.warn("content.clova-stt.audio-convert.failed: ffmpeg exited with code {}. output={}", exitCode, ffmpegOutput);
                throw new BusinessException(ErrorCode.INVALID_AUDIO_FILE);
            }
            return Files.readAllBytes(output);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new BusinessException(ErrorCode.STT_FAILED, exception);
        } catch (IOException exception) {
            log.warn(
                    "content.clova-stt.audio-convert.io-failed: audio to wav conversion failed. ffmpegPath={}",
                    properties.ffmpegPath(),
                    exception
            );
            throw new BusinessException(ErrorCode.STT_FAILED, exception);
        } finally {
            deleteIfExists(input);
            deleteIfExists(output);
        }
    }

    private void deleteIfExists(Path path) {
        if (path == null) {
            return;
        }
        try {
            Files.deleteIfExists(path);
        } catch (IOException exception) {
            log.debug("content.clova-stt.audio-convert.cleanup-failed: path={}", path, exception);
        }
    }
}
