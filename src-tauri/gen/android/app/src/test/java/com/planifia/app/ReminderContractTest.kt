package com.planifia.app

import app.tauri.notification.Notification
import app.tauri.notification.NotificationSchedule
import com.fasterxml.jackson.databind.ObjectMapper
import org.junit.Assert.*
import org.junit.Test
import java.time.Instant

class ReminderContractTest {
    @Test
    fun storedReminderCanBeRestoredWithoutTheWebview() {
        // El receptor de reinicio usa ObjectMapper sin la configuración extra del puente Tauri.
        val json = """{"id":7,"title":"Entrega mañana","body":"Historia","icon":"ic_notification","iconColor":"#10796c","visibility":0,"autoCancel":true,"schedule":{"at":{"date":"2026-09-25T12:00:00.000Z","repeating":false,"allowWhileIdle":true}}}"""
        val notification = ObjectMapper().readValue(json, Notification::class.java)
        assertEquals(7, notification.id)
        assertTrue(notification.isAutoCancel)
        assertEquals("ic_notification", notification.icon)
        val schedule = notification.schedule as NotificationSchedule.At
        assertTrue(schedule.allowWhileIdle)
        assertFalse(schedule.repeating)
        assertEquals(Instant.parse("2026-09-25T12:00:00Z").toEpochMilli(), schedule.date.time)
    }
}
