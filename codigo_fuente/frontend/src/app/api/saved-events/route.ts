import { NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "../auth/[...nextauth]/route";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

// GET: Obtener todos los eventIds guardados por el usuario actual
export async function GET() {
  const session = await getServerSession(authOptions);

  if (!session || !session.user || !(session.user as { id?: string }).id) {
    return NextResponse.json({ error: "No autorizado" }, { status: 401 });
  }

  const userId = (session.user as { id: string }).id;

  try {
    const savedEvents = await prisma.savedEvent.findMany({
      where: { userId },
      select: { eventId: true }
    });

    const eventIds = savedEvents.map(se => se.eventId);
    return NextResponse.json({ eventIds });
  } catch (error) {
    console.error("Error al obtener eventos guardados:", error);
    return NextResponse.json(
      { error: "Error interno del servidor" },
      { status: 500 }
    );
  }
}

// POST: Alternar (toggle) el estado de guardar un evento
export async function POST(request: Request) {
  const session = await getServerSession(authOptions);

  if (!session || !session.user || !(session.user as { id?: string }).id) {
    return NextResponse.json({ error: "No autorizado" }, { status: 401 });
  }

  const userId = (session.user as { id: string }).id;

  try {
    const { eventId } = await request.json();

    if (!eventId) {
      return NextResponse.json({ error: "ID de evento requerido" }, { status: 400 });
    }

    // Verificar si ya está guardado
    const existing = await prisma.savedEvent.findUnique({
      where: {
        userId_eventId: {
          userId,
          eventId
        }
      }
    });

    if (existing) {
      // Si existe, lo eliminamos (toggle off)
      await prisma.savedEvent.delete({
        where: {
          userId_eventId: {
            userId,
            eventId
          }
        }
      });
      return NextResponse.json({ saved: false, message: "Evento eliminado de tus guardados." });
    } else {
      // Si no existe, lo creamos (toggle on)
      await prisma.savedEvent.create({
        data: {
          userId,
          eventId
        }
      });
      return NextResponse.json({ saved: true, message: "Evento guardado con éxito." });
    }
  } catch (error) {
    console.error("Error al guardar/eliminar evento:", error);
    return NextResponse.json(
      { error: "Error interno del servidor" },
      { status: 500 }
    );
  }
}
