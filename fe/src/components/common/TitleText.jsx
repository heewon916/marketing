function TitleText({ text, className = "" }) {
  return (
    <h1
      className={`text-center text-[28px] font-bold text-gray-900 ${className} leading-snug`}
      style={{ wordBreak: "keep-all" }}
    >
      {text}
    </h1>
  )
}

export default TitleText
