import { NextRequest } from "next/server";
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(req: NextRequest) {
  const { name, email, message } = await req.json();

  try {
    const data = await resend.emails.send({
      from: "onboarding@resend.dev", // use your verified sender
      to: email,
      subject: `Thanks for contacting us, ${name}!`,
      html: `
        <p>Hi <strong>${name}</strong>,</p>
        <p>Thank you for reaching out on propelius.tech ! We received your message:</p>
        <blockquote>${message}</blockquote>
        <p>We’ll get back to you shortly.</p>
        <p>— Your AI Agent Team 🤖</p>
      `,
    });

    return Response.json({ success: true, data });
  } catch (error) {
    console.error("Resend error:", error);
    return Response.json({ error: "Failed to send" }, { status: 500 });
  }
}
