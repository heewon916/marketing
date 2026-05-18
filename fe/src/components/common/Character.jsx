import CharacterCamera from "@/assets/character/CharacterCamera.mp4"
import CharacterDdabong from "@/assets/character/CharacterDdabong.mp4"
import CharacterFail from "@/assets/character/CharacterFail.mp4"
import CharacterListen from "@/assets/character/CharacterListen.mp4"
import CharacterLove from "@/assets/character/CharacterLove.mp4"
import CharacterRun from "@/assets/character/CharacterRun.mp4"

export const CHARACTER = {
  camera: CharacterCamera,
  ddabong: CharacterDdabong,
  fail: CharacterFail,
  listen: CharacterListen,
  love: CharacterLove,
  run: CharacterRun,
}

function Character({ type, src, onClick, className = "" }) {
  const videoSrc = src ?? CHARACTER[type] ?? CHARACTER.ddabong

  return (
    <video
      src={videoSrc}
      alt="똑디 캐릭터"
      className={`object-contain ${className}`}
      onClick={onClick}
      autoPlay
      loop
      muted
      playsInline
    />
  )
}

export default Character
