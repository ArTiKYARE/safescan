'use client';

import React from 'react';
import DashboardLayout from '@/components/layout/dashboard-layout';
import { Breadcrumbs } from '@/components/ui/breadcrumbs';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <DashboardLayout>
      <div className="p-6 max-w-7xl mx-auto">
        <Breadcrumbs />
        {children}
      </div>
    </DashboardLayout>
  );
}
