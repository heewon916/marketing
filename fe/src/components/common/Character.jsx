import CharacterCamera from "@/assets/character/CharacterCamera.png"
import CharacterDdabong from "@/assets/character/CharacterDdabong.png"
import CharacterFail from "@/assets/character/CharacterFail.png"
import CharacterListen from "@/assets/character/CharacterListen.png"
import CharacterLove from "@/assets/character/CharacterLove.png"
import CharacterRun from "@/assets/character/CharacterRun.png"

export const CHARACTER = {
  camera: CharacterCamera,
  ddabong: CharacterDdabong,
  fail: CharacterFail,
  listen: CharacterListen,
  love: CharacterLove,
  run: CharacterRun,
}

function Character({ type, src, onClick, className = "" }) {
  const imageSrc = src ?? CHARACTER[type] ?? CHARACTER.ddabong

  return (
    <img
      src={imageSrc}
      alt="똑디 캐릭터"
      className={`object-contain ${className}`}
      onClick={onClick}
    />
  )
}

export default Character
