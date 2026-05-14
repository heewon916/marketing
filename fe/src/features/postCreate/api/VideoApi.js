import { api } from "@/lib/Axios"

export async function requestVideoUpload(videoFile, sessionId) {
	if (!videoFile) {
		throw new Error("업로드할 영상 파일이 없습니다.")
	}

	if (!sessionId) {
        console.log("세션 정보가 없어 영상 업로드를 진행할 수 없습니다.")
		//throw new Error("세션 정보가 없어 영상 업로드를 진행할 수 없습니다.")
	}

	try {
		const formData = new FormData()
		formData.append("video_file", videoFile)
		console.log("보내는 비디오파일:", videoFile)
		console.log("보내는 formData:", formData)

		const response = await api.post(`/api/v1/contents/${sessionId}/video`, formData, {
			headers: {
				"Content-Type": "multipart/form-data",
			},
		})

		const data = response.data ?? {}
		console.log(data)
		console.log("다음으로 넘어감")
		
		// extracted_frames의 original_key에 CloudFront 도메인 붙이기
		if (Array.isArray(data.extracted_frames)) {
			data.extracted_frames = data.extracted_frames.map(frame => ({
				...frame,
				original_key: frame.original_key ? `${import.meta.env.VITE_CLOUDFRONT_DOMAIN}${frame.original_key}` : ""
			}))
		}
		
		return data
	} catch (error) {
		const errorMessage = error.response?.data?.message
		console.log(error.response.data)
		throw new Error(errorMessage || "영상 업로드에 실패했습니다.", { cause: error })
	}
}
