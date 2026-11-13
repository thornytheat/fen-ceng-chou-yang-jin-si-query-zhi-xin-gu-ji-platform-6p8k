import { useCallback, useState } from 'react';

/** 轻量异步动作包装：busy + error，供按钮禁用与错误提示复用。 */
export function useAsync<Args extends unknown[], Result>(
  action: (...args: Args) => Promise<Result>,
) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>('');

  const run = useCallback(
    async (...args: Args): Promise<Result | null> => {
      setBusy(true);
      setError('');
      try {
        return await action(...args);
      } catch (err) {
        const payload = (err as { payload?: unknown }).payload;
        const message =
          payload && typeof payload === 'object' && 'message' in payload
            ? String((payload as { message?: string }).message)
            : '请求失败';
        setError(message);
        return null;
      } finally {
        setBusy(false);
      }
    },
    [action],
  );

  return { run, busy, error, setError };
}
