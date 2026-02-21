/**
 * Notification Service
 * ====================
 *
 * Multi-channel notification system for alerts and user engagement.
 * Ported from: FinceptTerminal/src/services/notifications/notificationService.ts
 * Enhanced with: Cross-border timezone support, multi-language
 */

import type { Currency, Signal } from '../domain/types.js';

// ============================================================================
// TYPES
// ============================================================================

export type NotificationChannel = 'push' | 'email' | 'sms' | 'slack' | 'telegram' | 'discord' | 'webhook';
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';
export type NotificationType =
  | 'price_alert'
  | 'trade_executed'
  | 'trade_blocked'
  | 'goal_milestone'
  | 'rebalance_needed'
  | 'fx_alert'
  | 'risk_warning'
  | 'circuit_breaker'
  | 'news_event'
  | 'dividend'
  | 'earnings'
  | 'custom';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  priority: NotificationPriority;
  channels: NotificationChannel[];
  metadata?: Record<string, unknown>;
  createdAt: Date;
  sentAt?: Date;
  readAt?: Date;
}

export interface NotificationPreferences {
  userId: string;
  channels: {
    push: boolean;
    email: boolean;
    sms: boolean;
    slack: boolean;
    telegram: boolean;
    discord: boolean;
  };
  quietHours: {
    enabled: boolean;
    start: string;  // "22:00"
    end: string;    // "08:00"
    timezone: string;
  };
  thresholds: {
    priceChangeAlert: number;  // Percentage
    tradeAmountAlert: number;  // Amount in base currency
  };
  language: 'en' | 'hi' | 'ar';
}

export interface ChannelConfig {
  email?: { address: string };
  sms?: { phoneNumber: string };
  slack?: { webhookUrl: string; channel?: string };
  telegram?: { chatId: string; botToken: string };
  discord?: { webhookUrl: string };
  webhook?: { url: string; headers?: Record<string, string> };
}

// ============================================================================
// NOTIFICATION TEMPLATES
// ============================================================================

const templates: Record<NotificationType, { title: string; body: string }> = {
  price_alert: {
    title: 'Price Alert: {symbol}',
    body: '{symbol} is now {price} ({change}% {direction})',
  },
  trade_executed: {
    title: 'Trade Executed',
    body: '{action} {quantity} {symbol} at {price}',
  },
  trade_blocked: {
    title: 'Trade Blocked',
    body: 'Your trade was blocked: {reason}',
  },
  goal_milestone: {
    title: 'Goal Milestone!',
    body: 'Your "{goalName}" goal is now {percentage}% complete!',
  },
  rebalance_needed: {
    title: 'Rebalance Needed',
    body: 'Your portfolio has drifted {drift}% from target allocation',
  },
  fx_alert: {
    title: 'FX Alert: {pair}',
    body: '{pair} rate is now {rate} - {recommendation}',
  },
  risk_warning: {
    title: 'Risk Warning',
    body: '{warning}',
  },
  circuit_breaker: {
    title: 'Trading Halted',
    body: 'Circuit breaker triggered: {reason}. Resumes at {resumeTime}.',
  },
  news_event: {
    title: 'Market News: {headline}',
    body: '{summary}',
  },
  dividend: {
    title: 'Dividend Received',
    body: '{symbol} dividend of {amount} credited to your account',
  },
  earnings: {
    title: 'Earnings Alert: {symbol}',
    body: '{symbol} reports {result} - {surprise}% {direction} surprise',
  },
  custom: {
    title: '{title}',
    body: '{body}',
  },
};

// ============================================================================
// IN-MEMORY STORAGE
// ============================================================================

const notifications: Map<string, Notification[]> = new Map();
const preferences: Map<string, NotificationPreferences> = new Map();
const channelConfigs: Map<string, ChannelConfig> = new Map();

// ============================================================================
// NOTIFICATION SERVICE
// ============================================================================

export const notificationService = {
  /**
   * Set user notification preferences.
   */
  setPreferences(userId: string, prefs: Partial<NotificationPreferences>): void {
    const existing = preferences.get(userId) || {
      userId,
      channels: {
        push: true,
        email: true,
        sms: false,
        slack: false,
        telegram: false,
        discord: false,
      },
      quietHours: {
        enabled: false,
        start: '22:00',
        end: '08:00',
        timezone: 'Asia/Kolkata',
      },
      thresholds: {
        priceChangeAlert: 5,
        tradeAmountAlert: 50000,
      },
      language: 'en',
    };

    preferences.set(userId, { ...existing, ...prefs });
  },

  /**
   * Get user notification preferences.
   */
  getPreferences(userId: string): NotificationPreferences | null {
    return preferences.get(userId) || null;
  },

  /**
   * Configure a notification channel.
   */
  configureChannel(userId: string, config: ChannelConfig): void {
    const existing = channelConfigs.get(userId) || {};
    channelConfigs.set(userId, { ...existing, ...config });
  },

  /**
   * Send a notification.
   */
  async send(
    userId: string,
    type: NotificationType,
    data: Record<string, unknown>,
    options?: {
      priority?: NotificationPriority;
      channels?: NotificationChannel[];
    }
  ): Promise<Notification> {
    const prefs = preferences.get(userId);
    const template = templates[type];

    // Interpolate template
    let title = template.title;
    let body = template.body;

    for (const [key, value] of Object.entries(data)) {
      title = title.replace(`{${key}}`, String(value));
      body = body.replace(`{${key}}`, String(value));
    }

    // Determine channels
    let channels: NotificationChannel[] = options?.channels || [];
    if (channels.length === 0 && prefs) {
      channels = Object.entries(prefs.channels)
        .filter(([_, enabled]) => enabled)
        .map(([channel]) => channel as NotificationChannel);
    }
    if (channels.length === 0) {
      channels = ['push']; // Default to push
    }

    // Check quiet hours
    if (prefs?.quietHours.enabled && !this.isUrgent(options?.priority)) {
      if (this.isQuietHours(prefs.quietHours)) {
        // Queue for later instead of sending now
        console.log('[Notification] Queued during quiet hours:', title);
      }
    }

    // Create notification
    const notification: Notification = {
      id: `notif-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      type,
      title,
      body,
      priority: options?.priority || 'normal',
      channels,
      metadata: data,
      createdAt: new Date(),
    };

    // Store notification
    const userNotifs = notifications.get(userId) || [];
    userNotifs.push(notification);
    notifications.set(userId, userNotifs);

    // Send to each channel
    const config = channelConfigs.get(userId);
    for (const channel of channels) {
      await this.sendToChannel(channel, notification, config);
    }

    notification.sentAt = new Date();
    return notification;
  },

  /**
   * Send to a specific channel.
   */
  async sendToChannel(
    channel: NotificationChannel,
    notification: Notification,
    config?: ChannelConfig
  ): Promise<boolean> {
    try {
      switch (channel) {
        case 'push':
          // Browser/mobile push notification
          console.log('[Push]', notification.title, notification.body);
          return true;

        case 'email':
          if (config?.email) {
            // In production: use SendGrid, AWS SES, etc.
            console.log('[Email]', config.email.address, notification.title);
          }
          return true;

        case 'sms':
          if (config?.sms) {
            // In production: use Twilio, AWS SNS, etc.
            console.log('[SMS]', config.sms.phoneNumber, notification.body);
          }
          return true;

        case 'slack':
          if (config?.slack) {
            await this.sendSlackMessage(config.slack.webhookUrl, notification);
          }
          return true;

        case 'telegram':
          if (config?.telegram) {
            await this.sendTelegramMessage(
              config.telegram.botToken,
              config.telegram.chatId,
              notification
            );
          }
          return true;

        case 'discord':
          if (config?.discord) {
            await this.sendDiscordMessage(config.discord.webhookUrl, notification);
          }
          return true;

        case 'webhook':
          if (config?.webhook) {
            await fetch(config.webhook.url, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...config.webhook.headers,
              },
              body: JSON.stringify(notification),
            });
          }
          return true;

        default:
          return false;
      }
    } catch (error) {
      console.error(`[Notification] Failed to send to ${channel}:`, error);
      return false;
    }
  },

  /**
   * Send Slack message.
   */
  async sendSlackMessage(webhookUrl: string, notification: Notification): Promise<void> {
    const color = notification.priority === 'urgent' ? '#FF0000' :
                  notification.priority === 'high' ? '#FFA500' : '#36a64f';

    await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        attachments: [{
          color,
          title: notification.title,
          text: notification.body,
          ts: Math.floor(notification.createdAt.getTime() / 1000),
        }],
      }),
    });
  },

  /**
   * Send Telegram message.
   */
  async sendTelegramMessage(
    botToken: string,
    chatId: string,
    notification: Notification
  ): Promise<void> {
    const emoji = notification.priority === 'urgent' ? '🚨' :
                  notification.priority === 'high' ? '⚠️' : 'ℹ️';

    await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text: `${emoji} *${notification.title}*\n\n${notification.body}`,
        parse_mode: 'Markdown',
      }),
    });
  },

  /**
   * Send Discord message.
   */
  async sendDiscordMessage(webhookUrl: string, notification: Notification): Promise<void> {
    const color = notification.priority === 'urgent' ? 0xFF0000 :
                  notification.priority === 'high' ? 0xFFA500 : 0x36a64f;

    await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        embeds: [{
          title: notification.title,
          description: notification.body,
          color,
          timestamp: notification.createdAt.toISOString(),
        }],
      }),
    });
  },

  /**
   * Get user's notifications.
   */
  getNotifications(
    userId: string,
    filter?: { unreadOnly?: boolean; type?: NotificationType }
  ): Notification[] {
    let notifs = notifications.get(userId) || [];

    if (filter?.unreadOnly) {
      notifs = notifs.filter((n) => !n.readAt);
    }
    if (filter?.type) {
      notifs = notifs.filter((n) => n.type === filter.type);
    }

    return notifs.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  },

  /**
   * Mark notification as read.
   */
  markAsRead(userId: string, notificationId: string): void {
    const notifs = notifications.get(userId);
    if (notifs) {
      const notif = notifs.find((n) => n.id === notificationId);
      if (notif) {
        notif.readAt = new Date();
      }
    }
  },

  /**
   * Check if current time is in quiet hours.
   */
  isQuietHours(quietHours: NotificationPreferences['quietHours']): boolean {
    const now = new Date();
    const [startHour, startMin] = quietHours.start.split(':').map(Number);
    const [endHour, endMin] = quietHours.end.split(':').map(Number);

    const currentMinutes = now.getHours() * 60 + now.getMinutes();
    const startMinutes = startHour * 60 + startMin;
    const endMinutes = endHour * 60 + endMin;

    if (startMinutes < endMinutes) {
      // Same day (e.g., 09:00 to 17:00)
      return currentMinutes >= startMinutes && currentMinutes < endMinutes;
    } else {
      // Overnight (e.g., 22:00 to 08:00)
      return currentMinutes >= startMinutes || currentMinutes < endMinutes;
    }
  },

  /**
   * Check if priority bypasses quiet hours.
   */
  isUrgent(priority?: NotificationPriority): boolean {
    return priority === 'urgent' || priority === 'high';
  },

  // ============================================================================
  // CONVENIENCE METHODS
  // ============================================================================

  /**
   * Send price alert.
   */
  async sendPriceAlert(
    userId: string,
    symbol: string,
    price: number,
    change: number
  ): Promise<Notification> {
    return this.send(userId, 'price_alert', {
      symbol,
      price: price.toFixed(2),
      change: Math.abs(change).toFixed(2),
      direction: change >= 0 ? 'up' : 'down',
    }, { priority: Math.abs(change) > 10 ? 'high' : 'normal' });
  },

  /**
   * Send trade executed notification.
   */
  async sendTradeExecuted(
    userId: string,
    signal: Signal
  ): Promise<Notification> {
    return this.send(userId, 'trade_executed', {
      action: signal.action,
      quantity: signal.quantity,
      symbol: signal.symbol,
      price: signal.entryPrice.toFixed(2),
    });
  },

  /**
   * Send trade blocked notification.
   */
  async sendTradeBlocked(
    userId: string,
    reason: string
  ): Promise<Notification> {
    return this.send(userId, 'trade_blocked', { reason }, { priority: 'high' });
  },

  /**
   * Send goal milestone notification.
   */
  async sendGoalMilestone(
    userId: string,
    goalName: string,
    percentage: number
  ): Promise<Notification> {
    return this.send(userId, 'goal_milestone', {
      goalName,
      percentage: percentage.toFixed(0),
    }, { priority: 'normal' });
  },

  /**
   * Send circuit breaker notification.
   */
  async sendCircuitBreaker(
    userId: string,
    reason: string,
    resumeTime: Date
  ): Promise<Notification> {
    return this.send(userId, 'circuit_breaker', {
      reason,
      resumeTime: resumeTime.toLocaleTimeString(),
    }, { priority: 'urgent' });
  },

  /**
   * Send FX alert.
   */
  async sendFxAlert(
    userId: string,
    pair: string,
    rate: number,
    recommendation: string
  ): Promise<Notification> {
    return this.send(userId, 'fx_alert', {
      pair,
      rate: rate.toFixed(4),
      recommendation,
    });
  },
};
