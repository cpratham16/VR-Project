export const fieldBorderCls = (hasError?: boolean) =>
  hasError
    ? 'border-red-300 focus:border-red-500 focus:ring-red-500/10'
    : 'border-[#e8e4df] hover:border-[#d6cfc7] focus:border-accent focus:ring-accent/15';
