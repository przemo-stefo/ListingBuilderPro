// src/components/landing/AlertsSection.tsx
// Purpose: Marketplace + E-commerce alert groups (2x6 cards)
// NOT for: Feature cards or comparison table

'use client';

import { motion } from 'framer-motion';
import {
  AlertTriangle, Shield, ShoppingCart, FileWarning, Battery, Bell,
  Store, Receipt, Truck, ShieldAlert, Package, Globe,
} from 'lucide-react';
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/animations';
import { marketplaceAlerts, ecommerceAlerts } from '@/lib/landing-data';

const iconMap: Record<string, React.ElementType> = {
  AlertTriangle, Shield, ShoppingCart, FileWarning, Battery, Bell,
  Store, Receipt, Truck, ShieldAlert, Package, Globe,
};

interface AlertGroupProps {
  icon: React.ElementType;
  title: string;
  subtitle: string;
  alerts: typeof marketplaceAlerts;
}

function AlertGroup({ icon: GroupIcon, title, subtitle, alerts }: AlertGroupProps) {
  return (
    <div>
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
          <GroupIcon className="h-5 w-5 text-green-500" />
        </div>
        <div>
          <h3 className="font-semibold text-white">{title}</h3>
          <p className="text-sm text-neutral-500">{subtitle}</p>
        </div>
      </div>

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3"
      >
        {alerts.map((alert) => {
          const Icon = iconMap[alert.icon];
          return (
            <motion.div
              key={alert.title}
              variants={staggerItem}
              className="rounded-lg border border-border bg-[#1A1A1A] p-5"
            >
              <div className="mb-3 flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-green-500/10">
                  <Icon className="h-4 w-4 text-green-400" />
                </div>
                <h4 className="text-sm font-semibold text-white">{alert.title}</h4>
              </div>
              <p className="text-sm text-neutral-400">{alert.description}</p>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}

export function AlertsSection() {
  return (
    <section className="bg-[#121212] px-4 py-24 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mb-16 text-center"
        >
          <span className="text-sm font-medium tracking-wider text-green-500">SMART ALERTS</span>
          <h2 className="mt-3 text-3xl font-bold text-white sm:text-4xl">
            Customizable Alerts for{' '}
            <span className="text-green-500">Every Seller Type</span>
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-neutral-400">
            Stay ahead of compliance issues with intelligent alerts tailored to your sales channels.
          </p>
        </motion.div>

        {/* Two alert groups with vertical spacing */}
        <div className="space-y-16">
          <AlertGroup
            icon={ShoppingCart}
            title="Marketplace Sellers"
            subtitle="Amazon, eBay, Kaufland, Otto, Allegro"
            alerts={marketplaceAlerts}
          />
          <AlertGroup
            icon={Store}
            title="E-commerce & Online Stores"
            subtitle="Shopify, WooCommerce, Magento, PrestaShop"
            alerts={ecommerceAlerts}
          />
        </div>
      </div>
    </section>
  );
}
