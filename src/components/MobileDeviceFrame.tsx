import React from 'react';

interface MobileDeviceFrameProps {
  children: React.ReactNode;
  activeScreenTitle?: string;
  onOpenFlutterArchitecture?: () => void;
}

export const MobileDeviceFrame: React.FC<MobileDeviceFrameProps> = ({ children }) => {
  return (
    <div className="fixed inset-0 w-full h-full overflow-hidden bg-slate-950 flex flex-col items-center justify-center">
      {/* Mobile App Canvas Container - fills height up to screen boundaries */}
      <div className="w-full max-w-md h-full flex flex-col overflow-hidden bg-[#F8FAFC] shadow-2xl relative">
        {children}
      </div>
    </div>
  );
};
