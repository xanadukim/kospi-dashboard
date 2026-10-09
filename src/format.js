const getDayName = (dateStr) => {
  try {
    const daysEn = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const daysKr = ["일", "월", "화", "수", "목", "금", "토"];
    const d = new Date(dateStr + "T12:00:00");
    const day = d.getDay();
    return `${daysEn[day]} (${daysKr[day]})`;
  } catch {
    return "";
  }
};

if (typeof window !== 'undefined') window.getDayName = getDayName;
