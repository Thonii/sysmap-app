import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const { name, email, company, eventUrl, notes } = await request.json();

    if (!name || !email) {
      return NextResponse.json(
        { error: "El nombre y el correo electrónico son campos obligatorios." },
        { status: 400 }
      );
    }

    // Guardar lead en la base de datos
    const lead = await prisma.lead.create({
      data: {
        name,
        email,
        company: company || null,
        eventUrl: eventUrl || null,
        notes: notes || null,
      },
    });

    return NextResponse.json({
      success: true,
      message: "Lead registrado con éxito.",
      lead,
    });
  } catch (error) {
    console.error("Error al registrar lead B2B:", error);
    return NextResponse.json(
      { error: "Ocurrió un error interno en el servidor." },
      { status: 500 }
    );
  }
}
