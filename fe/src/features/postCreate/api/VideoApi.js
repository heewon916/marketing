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

		const response = await api.post(`/api/v1/contents/${sessionId}/video`, formData, {
			headers: {
				"Content-Type": "multipart/form-data",
			},
		})

		return response.data ?? {}
	} catch (error) {
		// const errorMessage = error.response?.data?.message
		// throw new Error(errorMessage || "영상 업로드에 실패했습니다.", { cause: error })
	}
}
