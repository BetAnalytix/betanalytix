import { NextRequest, NextResponse } from 'next/server'

const TOKEN = process.env.TELEGRAM_BOT_TOKEN!
const TELEGRAM_API = `https://api.telegram.org/bot${TOKEN}`

export async function POST(req: NextRequest) {
  const body = await req.json()
  const { chatId, message } = body

  if (!chatId || !message) {
    return NextResponse.json({ error: 'chatId and message required' }, { status: 400 })
  }

  const res = await fetch(`${TELEGRAM_API}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text: message,
      parse_mode: 'HTML',
    }),
  })

  const data = await res.json()
  return NextResponse.json(data)
}

export async function GET() {
  const res = await fetch(`${TELEGRAM_API}/getMe`)
  const data = await res.json()
  return NextResponse.json(data)
}
