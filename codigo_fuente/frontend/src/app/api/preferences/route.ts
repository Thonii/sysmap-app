import { NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "../auth/[...nextauth]/route";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

export async function GET() {
  const session = await getServerSession(authOptions);
  
  if (!session || !session.user || !(session.user as any).id) {
    return NextResponse.json({ error: "No autorizado" }, { status: 401 });
  }

  const userId = (session.user as any).id;

  try {
    const preferences = await prisma.userPreference.findUnique({
      where: { userId },
    });

    if (!preferences) {
      return NextResponse.json({
        tags: [],
        radiusKm: 15.0,
        latitude: null,
        longitude: null,
      });
    }

    return NextResponse.json({
      tags: JSON.parse(preferences.tags),
      radiusKm: preferences.radiusKm,
      latitude: preferences.latitude,
      longitude: preferences.longitude,
    });
  } catch (error) {
    console.error("Error obteniendo preferencias:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);

  if (!session || !session.user || !(session.user as any).id) {
    return NextResponse.json({ error: "No autorizado" }, { status: 401 });
  }

  const userId = (session.user as any).id;

  try {
    const { tags, radiusKm, latitude, longitude } = await request.json();

    const tagsString = JSON.stringify(tags || []);

    const updated = await prisma.userPreference.upsert({
      where: { userId },
      update: {
        tags: tagsString,
        radiusKm: radiusKm ?? 15.0,
        latitude,
        longitude,
      },
      create: {
        userId,
        tags: tagsString,
        radiusKm: radiusKm ?? 15.0,
        latitude,
        longitude,
      },
    });

    return NextResponse.json({
      success: true,
      preferences: {
        tags: JSON.parse(updated.tags),
        radiusKm: updated.radiusKm,
        latitude: updated.latitude,
        longitude: updated.longitude,
      },
    });
  } catch (error) {
    console.error("Error guardando preferencias:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
