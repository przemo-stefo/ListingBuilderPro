// frontend/src/lib/api/teams.ts
// Purpose: API calls for team workspace (CRUD, invitations, members)
// NOT for: React hooks or UI components

import { apiRequest } from './client'

export interface TeamInfo {
  id: number
  name: string
  owner_id: string
  member_count: number
  my_role: string
  created_at: string
}

export interface TeamMember {
  id: number
  user_id: string
  email: string
  role: string
  joined_at: string
}

export interface TeamInvitation {
  id: number
  email: string
  role: string
  token: string
  invited_by: string
  created_at: string
  expires_at: string
}

// --- Team CRUD ---

export async function listMyTeams(): Promise<TeamInfo[]> {
  const res = await apiRequest<TeamInfo[]>('get', '/teams')
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function createTeam(name: string): Promise<{ id: number; name: string }> {
  const res = await apiRequest<{ id: number; name: string }>('post', '/teams', { name })
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function updateTeam(teamId: number, name: string): Promise<void> {
  const res = await apiRequest<{ ok: boolean }>('patch', `/teams/${teamId}`, { name })
  if (res.error) throw new Error(res.error)
}

export async function deleteTeam(teamId: number): Promise<void> {
  const res = await apiRequest<void>('delete', `/teams/${teamId}`)
  if (res.error) throw new Error(res.error)
}

// --- Members ---

export async function listMembers(teamId: number): Promise<TeamMember[]> {
  const res = await apiRequest<TeamMember[]>('get', `/teams/${teamId}/members`)
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function updateMemberRole(teamId: number, memberId: number, role: string): Promise<void> {
  const res = await apiRequest<{ ok: boolean }>('patch', `/teams/${teamId}/members/${memberId}`, { role })
  if (res.error) throw new Error(res.error)
}

export async function removeMember(teamId: number, memberId: number): Promise<void> {
  const res = await apiRequest<void>('delete', `/teams/${teamId}/members/${memberId}`)
  if (res.error) throw new Error(res.error)
}

// --- Invitations ---

export async function createInvitation(teamId: number, email: string, role: string = 'editor'): Promise<{ token: string; expires_at: string }> {
  const res = await apiRequest<{ token: string; expires_at: string }>('post', `/teams/${teamId}/invitations`, { email, role })
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function listInvitations(teamId: number): Promise<TeamInvitation[]> {
  const res = await apiRequest<TeamInvitation[]>('get', `/teams/${teamId}/invitations`)
  if (res.error) throw new Error(res.error)
  return res.data!
}

export async function revokeInvitation(teamId: number, invitationId: number): Promise<void> {
  const res = await apiRequest<void>('delete', `/teams/${teamId}/invitations/${invitationId}`)
  if (res.error) throw new Error(res.error)
}

export async function acceptInvitation(token: string): Promise<{ team_id: number; team_name: string; role: string }> {
  const res = await apiRequest<{ team_id: number; team_name: string; role: string }>('post', `/teams/accept-invitation?token=${encodeURIComponent(token)}`)
  if (res.error) throw new Error(res.error)
  return res.data!
}
