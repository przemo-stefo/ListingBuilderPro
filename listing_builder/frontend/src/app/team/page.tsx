// frontend/src/app/team/page.tsx
// Purpose: Team workspace page — create, manage teams, invite members
// NOT for: Team-scoped resource filtering (that's per-route logic)

'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  UsersRound, Plus, Trash2, UserPlus, Shield, Eye, Edit3,
  Crown, Copy, Check, Mail, X, Loader2,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useToast } from '@/lib/hooks/useToast'
import { PremiumGate } from '@/components/tier/PremiumGate'
import {
  listMyTeams, createTeam, deleteTeam,
  listMembers, updateMemberRole, removeMember,
  createInvitation, listInvitations, revokeInvitation,
} from '@/lib/api/teams'
import type { TeamInfo, TeamMember, TeamInvitation } from '@/lib/api/teams'

const ROLE_LABELS: Record<string, string> = {
  owner: 'Wlasciciel',
  admin: 'Administrator',
  editor: 'Edytor',
  viewer: 'Podglad',
}

const ROLE_ICONS: Record<string, typeof Crown> = {
  owner: Crown,
  admin: Shield,
  editor: Edit3,
  viewer: Eye,
}

const ROLE_COLORS: Record<string, string> = {
  owner: 'bg-amber-500/10 text-amber-400',
  admin: 'bg-blue-500/10 text-blue-400',
  editor: 'bg-green-500/10 text-green-400',
  viewer: 'bg-gray-500/10 text-gray-400',
}

export default function TeamPage() {
  return (
    <PremiumGate feature="Team Workspace">
      <TeamContent />
    </PremiumGate>
  )
}

function TeamContent() {
  const { toast } = useToast()
  const [teams, setTeams] = useState<TeamInfo[]>([])
  const [selectedTeam, setSelectedTeam] = useState<TeamInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')

  const loadTeams = useCallback(async () => {
    try {
      const data = await listMyTeams()
      setTeams(data)
      if (data.length > 0 && !selectedTeam) {
        setSelectedTeam(data[0])
      }
    } catch {
      // WHY: First load fail shows empty state — no toast needed
    } finally {
      setLoading(false)
    }
  }, [selectedTeam])

  useEffect(() => { loadTeams() }, [loadTeams])

  const handleCreate = async () => {
    if (!newName.trim() || creating) return
    setCreating(true)
    try {
      const team = await createTeam(newName.trim())
      setNewName('')
      await loadTeams()
      setSelectedTeam({ id: team.id, name: team.name, owner_id: '', member_count: 1, my_role: 'owner', created_at: new Date().toISOString() })
    } catch (err) {
      toast({ title: 'Blad tworzenia zespolu', description: err instanceof Error ? err.message : 'Sprobuj ponownie', variant: 'destructive' })
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (teamId: number) => {
    if (!confirm('Na pewno usunac zespol? Tej operacji nie mozna cofnac.')) return
    try {
      await deleteTeam(teamId)
      if (selectedTeam?.id === teamId) setSelectedTeam(null)
      await loadTeams()
    } catch (err) {
      toast({ title: 'Blad usuwania', description: err instanceof Error ? err.message : 'Sprobuj ponownie', variant: 'destructive' })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <UsersRound className="h-6 w-6 text-gray-400" />
          <h1 className="text-xl font-semibold text-white">Zespol</h1>
        </div>
      </div>

      {/* Create team */}
      <Card>
        <CardContent className="flex items-center gap-3 p-4">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            placeholder="Nazwa nowego zespolu..."
            className="flex-1 rounded border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-gray-500 focus:outline-none"
            maxLength={100}
          />
          <Button size="sm" onClick={handleCreate} disabled={!newName.trim() || creating}>
            {creating ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Plus className="mr-1 h-4 w-4" />}
            Utworz zespol
          </Button>
        </CardContent>
      </Card>

      {teams.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-gray-400">
            Nie masz jeszcze zadnego zespolu. Utworz pierwszy powyzej.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          {/* Team list */}
          <div className="space-y-2">
            {teams.map((team) => (
              <button
                key={team.id}
                onClick={() => setSelectedTeam(team)}
                className={cn(
                  'flex w-full items-center justify-between rounded-lg border p-3 text-left transition-colors',
                  selectedTeam?.id === team.id
                    ? 'border-gray-600 bg-[#1A1A1A]'
                    : 'border-gray-800 hover:border-gray-700'
                )}
              >
                <div>
                  <p className="text-sm font-medium text-white">{team.name}</p>
                  <p className="text-xs text-gray-500">{team.member_count} czlonkow</p>
                </div>
                <Badge variant="secondary" className={cn('text-xs', ROLE_COLORS[team.my_role])}>
                  {ROLE_LABELS[team.my_role]}
                </Badge>
              </button>
            ))}
          </div>

          {/* Team detail */}
          {selectedTeam && (
            <TeamDetail
              team={selectedTeam}
              onDelete={() => handleDelete(selectedTeam.id)}
              onUpdate={loadTeams}
            />
          )}
        </div>
      )}
    </div>
  )
}

function TeamDetail({ team, onDelete, onUpdate }: { team: TeamInfo; onDelete: () => void; onUpdate: () => void }) {
  const { toast } = useToast()
  const [members, setMembers] = useState<TeamMember[]>([])
  const [invitations, setInvitations] = useState<TeamInvitation[]>([])
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('editor')
  const [inviting, setInviting] = useState(false)
  const [copiedToken, setCopiedToken] = useState<string | null>(null)

  const isOwnerOrAdmin = team.my_role === 'owner' || team.my_role === 'admin'

  const loadData = useCallback(async () => {
    try {
      const [m, i] = await Promise.all([
        listMembers(team.id),
        isOwnerOrAdmin ? listInvitations(team.id) : Promise.resolve([]),
      ])
      setMembers(m)
      setInvitations(i)
    } catch { /* */ }
  }, [team.id, isOwnerOrAdmin])

  useEffect(() => { loadData() }, [loadData])

  const handleInvite = async () => {
    if (!inviteEmail.trim() || inviting) return
    setInviting(true)
    try {
      await createInvitation(team.id, inviteEmail.trim(), inviteRole)
      setInviteEmail('')
      await loadData()
    } catch (err) {
      toast({ title: 'Blad zaproszenia', description: err instanceof Error ? err.message : 'Sprobuj ponownie', variant: 'destructive' })
    }
    finally { setInviting(false) }
  }

  const handleRoleChange = async (memberId: number, role: string) => {
    try {
      await updateMemberRole(team.id, memberId, role)
      await loadData()
    } catch (err) {
      toast({ title: 'Blad zmiany roli', description: err instanceof Error ? err.message : 'Sprobuj ponownie', variant: 'destructive' })
    }
  }

  const handleRemoveMember = async (memberId: number) => {
    if (!confirm('Usunac czlonka z zespolu?')) return
    try {
      await removeMember(team.id, memberId)
      await loadData()
      onUpdate()
    } catch (err) {
      toast({ title: 'Blad usuwania czlonka', description: err instanceof Error ? err.message : 'Sprobuj ponownie', variant: 'destructive' })
    }
  }

  const handleRevokeInvite = async (inviteId: number) => {
    try {
      await revokeInvitation(team.id, inviteId)
      await loadData()
    } catch (err) {
      toast({ title: 'Blad cofania zaproszenia', description: err instanceof Error ? err.message : 'Sprobuj ponownie', variant: 'destructive' })
    }
  }

  const copyInviteLink = (token: string) => {
    const url = `${window.location.origin}/team/accept?token=${token}`
    navigator.clipboard.writeText(url)
    setCopiedToken(token)
    setTimeout(() => setCopiedToken(null), 2000)
  }

  return (
    <div className="space-y-4">
      {/* Team header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{team.name}</CardTitle>
            {team.my_role === 'owner' && (
              <Button variant="outline" size="sm" className="text-red-400 hover:text-red-300" onClick={onDelete}>
                <Trash2 className="mr-1 h-3 w-3" /> Usun zespol
              </Button>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Invite */}
      {isOwnerOrAdmin && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Zapros czlonka</CardTitle></CardHeader>
          <CardContent className="flex items-center gap-3">
            <input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleInvite()}
              placeholder="email@example.com"
              className="flex-1 rounded border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-gray-500 focus:outline-none"
            />
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="rounded border border-gray-700 bg-[#1A1A1A] px-3 py-2 text-sm text-white"
            >
              <option value="admin">Administrator</option>
              <option value="editor">Edytor</option>
              <option value="viewer">Podglad</option>
            </select>
            <Button size="sm" onClick={handleInvite} disabled={!inviteEmail.trim() || inviting}>
              {inviting ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <UserPlus className="mr-1 h-4 w-4" />}
              Zapros
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Members */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Czlonkowie ({members.length})</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {members.map((m) => {
            const RoleIcon = ROLE_ICONS[m.role] || Eye
            return (
              <div key={m.id} className="flex items-center justify-between rounded-lg border border-gray-800 p-3">
                <div className="flex items-center gap-3">
                  <RoleIcon className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-sm text-white">{m.email}</p>
                    <Badge variant="secondary" className={cn('text-xs', ROLE_COLORS[m.role])}>
                      {ROLE_LABELS[m.role]}
                    </Badge>
                  </div>
                </div>
                {isOwnerOrAdmin && m.role !== 'owner' && (
                  <div className="flex items-center gap-2">
                    <select
                      value={m.role}
                      onChange={(e) => handleRoleChange(m.id, e.target.value)}
                      className="rounded border border-gray-700 bg-[#1A1A1A] px-2 py-1 text-xs text-white"
                    >
                      <option value="admin">Administrator</option>
                      <option value="editor">Edytor</option>
                      <option value="viewer">Podglad</option>
                    </select>
                    <Button variant="ghost" size="sm" onClick={() => handleRemoveMember(m.id)}>
                      <X className="h-3 w-3 text-gray-400 hover:text-red-400" />
                    </Button>
                  </div>
                )}
              </div>
            )
          })}
        </CardContent>
      </Card>

      {/* Pending invitations */}
      {isOwnerOrAdmin && invitations.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Oczekujace zaproszenia ({invitations.length})</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {invitations.map((inv) => (
              <div key={inv.id} className="flex items-center justify-between rounded-lg border border-gray-800 p-3">
                <div className="flex items-center gap-3">
                  <Mail className="h-4 w-4 text-gray-400" />
                  <div>
                    <p className="text-sm text-white">{inv.email}</p>
                    <p className="text-xs text-gray-500">
                      {ROLE_LABELS[inv.role]} — wygasa {new Date(inv.expires_at).toLocaleDateString('pl-PL')}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={() => copyInviteLink(inv.token)}>
                    {copiedToken === inv.token ? <Check className="h-3 w-3 text-green-400" /> : <Copy className="h-3 w-3 text-gray-400" />}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleRevokeInvite(inv.id)}>
                    <X className="h-3 w-3 text-gray-400 hover:text-red-400" />
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
