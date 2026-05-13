import { api } from "@/lib/Axios"

export async function requestContentImages(sessionId) {
	if (!sessionId) {
		//throw new Error("세션 정보가 없어 이미지를 조회할 수 없습니다.")
	}

	try {
		const response = await api.get(`/api/v1/contents/${sessionId}/images`)
		const data = response.data ?? {}
		const imageList = Array.isArray(data.image_url) ? data.image_url : []
		console.log(data)
		return {
			sessionId: data.session_id ?? sessionId,
			images: imageList.map((image, index) => ({
				id: image.image_key ?? `image-${index}`,
				imageKey: image.image_key ?? "",
				url: image.image_url ?? "",
			})),
		}
	} catch (error) {
		const errorMessage = error.response?.data?.message
		//throw new Error(errorMessage || "이미지 조회에 실패했습니다.", { cause: error })
	}
}

export async function requestDeleteContentImage(sessionId, deletedImageKey) {
	if (!sessionId) {
		throw new Error("세션 정보가 없어 이미지를 삭제할 수 없습니다.")
	}

	if (!deletedImageKey) {
		throw new Error("삭제할 이미지 키가 없습니다.")
	}

	try {
		const response = await api.post(`/api/v1/contents/${sessionId}/images/delete`, {
			session_id: sessionId,
			deleted_image_key: deletedImageKey,
		})

		const data = response.data ?? {}

		return {
			success: Boolean(data.success),
			remainingImages: Number.isFinite(data.remaining_images) ? data.remaining_images : null,
		}
	} catch (error) {
		const errorMessage = error.response?.data?.message
		//throw new Error(errorMessage || "이미지 삭제에 실패했습니다.", { cause: error })
	}
}
