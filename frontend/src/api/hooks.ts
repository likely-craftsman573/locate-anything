import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    // Poll quickly while the model loads so the UI flips to ready promptly.
    refetchInterval: (query) => (query.state.data?.status === "loading" ? 2000 : 15000),
  });
}

export function useTasks() {
  return useQuery({ queryKey: ["tasks"], queryFn: api.tasks, staleTime: Infinity });
}

export function useHistory() {
  return useQuery({ queryKey: ["history"], queryFn: () => api.history() });
}

export function useHistoryItem(id: string | null) {
  return useQuery({
    queryKey: ["history", id],
    queryFn: () => api.historyItem(id as string),
    enabled: !!id,
  });
}

export function useLocate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.locate,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["history"] }),
  });
}

export function useDeleteHistory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.deleteHistory,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["history"] }),
  });
}
