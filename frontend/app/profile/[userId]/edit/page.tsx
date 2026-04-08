'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Box, Flex, Spinner } from '@chakra-ui/react';
import { Navbar } from '@/components/layout/Navbar';
import { toast } from '@/lib/ui/toast';
import { getMe, patchMe } from '@/lib/api/users';
import type { AuthUser } from '@/lib/api/types/auth';
import type { UserPrivate } from '@/lib/api/types/user';
import { useAuth } from '@/components/domain/AuthProvider';
import {
  getInitials,
  loadExtendedProfile,
  saveExtendedProfile,
} from '../_utils/profileShared';
import { ProfileEditHeader } from './_components/ProfileEditHeader';
import { ProfileEditColumns } from './_components/ProfileEditColumns';

const inputBase: Record<string, unknown> = {
  border: '1px solid',
  borderColor: 'gray.300',
  borderRadius: '10px',
  px: '12px',
  bg: 'white',
  fontSize: 'sm',
  color: 'gray.900',
  w: '100%',
  outline: 'none',
  _focus: { borderColor: 'orange.400' },
} as const;

export default function EditProfilePage() {
  const router = useRouter();
  const { userId } = useParams<{ userId: string }>();
  const { user: authUser, isReady, updateCachedUser } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  /** Tracks blob: URLs from file picks only (not remote profile_picture_url). */
  const avatarObjectUrlRef = useRef<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [apiUser, setApiUser] = useState<UserPrivate | null>(null);

  const [name, setName] = useState('');
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

  const [bio, setBio] = useState('');
  const [github, setGithub] = useState('');
  const [linkedin, setLinkedin] = useState('');
  const [website, setWebsite] = useState('');
  const [major, setMajor] = useState('');
  const [gradYear, setGradYear] = useState('');
  const [courses, setCourses] = useState<string[]>([]);
  const [courseInput, setCourseInput] = useState('');
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState('');

  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [pwError, setPwError] = useState('');
  const [pwSuccess, setPwSuccess] = useState(false);

  useEffect(() => {
    if (!isReady) return;

    // Guard: only the owner can edit their own profile
    if (!authUser) {
      router.replace('/login');
      return;
    }
    if (authUser.id !== userId) {
      router.replace(`/profile/${userId}`);
      return;
    }

    async function load() {
      try {
        const user = await getMe();
        setApiUser(user);
        setName(user.full_name ?? '');
        avatarObjectUrlRef.current = null;
        if (user.profile_picture_url)
          setAvatarPreview(user.profile_picture_url);

        const ext = loadExtendedProfile(user.id);
        setBio(ext.bio);
        setGithub(ext.socials.github ?? '');
        setLinkedin(ext.socials.linkedin ?? '');
        setWebsite(ext.socials.website ?? '');
        setMajor(ext.major);
        setGradYear(ext.graduationYear > 0 ? String(ext.graduationYear) : '');
        setCourses(ext.courses);
        setSkills(ext.skills);
      } catch {
        toast.error({
          title: 'Could not load profile',
          description: 'Please try again.',
        });
        router.push(`/profile/${userId}`);
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [isReady, authUser, userId, router]);

  useEffect(() => {
    return () => {
      if (avatarObjectUrlRef.current) {
        URL.revokeObjectURL(avatarObjectUrlRef.current);
      }
    };
  }, []);

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const MAX_SIZE_BYTES = 5 * 1024 * 1024;
    if (file.size > MAX_SIZE_BYTES) {
      e.target.value = '';
      if (fileInputRef.current) fileInputRef.current.value = '';
      toast.error({
        id: String(Date.now()),
        title: 'Image too large',
        description: 'Please choose a file smaller than 5MB.',
        duration: 3000,
      });
      return;
    }

    e.target.value = '';
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (avatarObjectUrlRef.current) {
      URL.revokeObjectURL(avatarObjectUrlRef.current);
    }
    const url = URL.createObjectURL(file);
    avatarObjectUrlRef.current = url;
    setAvatarPreview(url);
  };

  const addCourse = () => {
    if (courseInput.trim()) {
      setCourses((p) => [...p, courseInput.trim()]);
      setCourseInput('');
    }
  };
  const removeCourse = (c: string) =>
    setCourses((p) => p.filter((x) => x !== c));

  const addSkill = () => {
    if (skillInput.trim()) {
      setSkills((p) => [...p, skillInput.trim()]);
      setSkillInput('');
    }
  };
  const removeSkill = (s: string) => setSkills((p) => p.filter((x) => x !== s));

  const pwButtonDisabled = !currentPw || !newPw || !confirmPw;
  const handleChangePassword = () => {
    setPwError('');
    setPwSuccess(false);
    if (newPw !== confirmPw) {
      setPwError('New passwords do not match.');
      return;
    }
    if (newPw.length < 12) {
      setPwError('New password must be at least 12 characters.');
      return;
    }
    toast.error({
      title: 'Not available yet',
      description: 'Password change requires a backend endpoint.',
    });
  };

  const handleSave = async () => {
    if (!apiUser) return;
    setSaving(true);
    try {
      const updated = await patchMe({ full_name: name.trim() || undefined });

      const nextAuth: AuthUser = {
        id: updated.id,
        email: updated.email,
        username: updated.username,
        role: updated.role,
        full_name: updated.full_name,
        profile_picture_url: updated.profile_picture_url,
      };
      updateCachedUser(nextAuth);

      saveExtendedProfile(apiUser.id, {
        bio,
        socials: {
          github: github || undefined,
          linkedin: linkedin || undefined,
          website: website || undefined,
        },
        major,
        graduationYear: Number(gradYear) || 0,
        courses,
        skills,
      });

      toast.success({
        title: 'Profile saved',
        description: 'Your changes have been saved.',
      });
      router.push(`/profile/${updated.id}`);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Could not save profile.';
      toast.error({ title: 'Save failed', description: message });
    } finally {
      setSaving(false);
    }
  };

  if (loading || !isReady) {
    return (
      <Box minH="100vh" bg="transparent">
        <Navbar />
        <Flex justify="center" align="center" minH="60vh">
          <Spinner size="lg" color="orange.400" />
        </Flex>
      </Box>
    );
  }

  if (!apiUser) return null;

  const displayName = apiUser.full_name ?? apiUser.email;

  return (
    <Box minH="100vh" bg="transparent">
      <Navbar />

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleAvatarChange}
      />

      <Box px="36px" pt="32px" pb="64px" maxW="1280px" mx="auto">
        <ProfileEditHeader
          avatarPreview={avatarPreview}
          displayName={displayName}
          name={name}
          bio={bio}
          github={github}
          linkedin={linkedin}
          website={website}
          role={apiUser.role as 'student' | 'faculty'}
          inputBase={inputBase}
          saving={saving}
          onNameChange={setName}
          onBioChange={setBio}
          onGithubChange={setGithub}
          onLinkedinChange={setLinkedin}
          onWebsiteChange={setWebsite}
          onAvatarClick={() => fileInputRef.current?.click()}
          onCancel={() => router.push(`/profile/${apiUser.id}`)}
          onSave={handleSave}
          getInitials={getInitials}
        />

        <ProfileEditColumns
          inputBase={inputBase}
          major={major}
          gradYear={gradYear}
          courseInput={courseInput}
          courses={courses}
          email={apiUser.email}
          currentPw={currentPw}
          newPw={newPw}
          confirmPw={confirmPw}
          pwError={pwError}
          pwSuccess={pwSuccess}
          pwButtonDisabled={pwButtonDisabled}
          skillInput={skillInput}
          skills={skills}
          onMajorChange={setMajor}
          onGradYearChange={setGradYear}
          onCourseInputChange={setCourseInput}
          onAddCourse={addCourse}
          onRemoveCourse={removeCourse}
          onCurrentPwChange={setCurrentPw}
          onNewPwChange={setNewPw}
          onConfirmPwChange={setConfirmPw}
          onChangePassword={handleChangePassword}
          onSkillInputChange={setSkillInput}
          onAddSkill={addSkill}
          onRemoveSkill={removeSkill}
        />
      </Box>
    </Box>
  );
}
