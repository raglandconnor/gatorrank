'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box,
  Flex,
  HStack,
  VStack,
  Text,
  Button,
  Wrap,
  Input,
  Textarea,
  Spinner,
} from '@chakra-ui/react';
import {
  LuX,
  LuSave,
  LuGithub,
  LuLinkedin,
  LuGlobe,
  LuMail,
  LuLock,
  LuEye,
  LuEyeOff,
  LuPlus,
  LuCamera,
  LuShieldCheck,
} from 'react-icons/lu';
import { Navbar } from '@/components/layout/Navbar';
import { toast } from '@/lib/ui/toast';
import { RoleBadge } from '@/components/ui/rolebadge';
import { getMe, patchMe } from '@/lib/api/users';
import type { AuthUser } from '@/lib/api/types/auth';
import type { UserPrivate } from '@/lib/api/types/user';
import { useAuth } from '@/components/domain/AuthProvider';
import {
  getInitials,
  loadExtendedProfile,
  saveExtendedProfile,
} from '../_utils/profileShared';

const inputBase = {
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

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <Text fontSize="sm" color="gray.500" lineHeight="24px">
      {children}
    </Text>
  );
}

function PasswordField({
  placeholder,
  value,
  onChange,
}: {
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const [show, setShow] = useState(false);
  return (
    <Box position="relative" w="100%">
      <Box
        position="absolute"
        left="12px"
        top="50%"
        transform="translateY(-50%)"
        color="gray.400"
        pointerEvents="none"
      >
        <LuLock size={16} />
      </Box>
      <Input
        type={show ? 'text' : 'password'}
        placeholder={placeholder}
        value={value}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          onChange(e.target.value)
        }
        {...inputBase}
        h="40px"
        pl="38px"
        pr="44px"
      />
      <Button
        aria-label="toggle password visibility"
        position="absolute"
        right="6px"
        top="50%"
        transform="translateY(-50%)"
        color="gray.400"
        onClick={() => setShow((v) => !v)}
        variant="ghost"
        _hover={{ color: 'gray.700' }}
        size="sm"
      >
        {show ? <LuEyeOff size={16} /> : <LuEye size={16} />}
      </Button>
    </Box>
  );
}

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
        {/* Profile hero */}
        <HStack gap="24px" mb="40px" align="flex-start">
          {/* Avatar */}
          <Box
            position="relative"
            w="96px"
            h="96px"
            flexShrink={0}
            cursor="pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            {avatarPreview ? (
              <img
                src={avatarPreview}
                alt={displayName}
                style={{
                  width: '96px',
                  height: '96px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  display: 'block',
                }}
              />
            ) : (
              <Flex
                w="96px"
                h="96px"
                borderRadius="full"
                bg="orange.400"
                color="white"
                align="center"
                justify="center"
                fontSize="2xl"
                fontWeight="bold"
              >
                {getInitials(displayName)}
              </Flex>
            )}
            <Box
              position="absolute"
              inset={0}
              borderRadius="full"
              bg="blackAlpha.500"
              display="flex"
              alignItems="center"
              justifyContent="center"
              opacity={0}
              _hover={{ opacity: 1 }}
              transition="opacity 0.15s"
              color="white"
            >
              <LuCamera size={22} />
            </Box>
          </Box>

          {/* Info VStack */}
          <VStack align="start" gap="10px" flex={1} minW={0}>
            <HStack gap="12px" align="center" w="100%" flexWrap="wrap">
              <Input
                value={name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setName(e.target.value)
                }
                placeholder="Your full name"
                {...inputBase}
                fontSize="xl"
                fontWeight="bold"
                h="47px"
                maxW="400px"
                lineHeight="32px"
              />
              <RoleBadge role={apiUser.role as 'student' | 'faculty'} />
            </HStack>

            <Textarea
              value={bio}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                setBio(e.target.value)
              }
              placeholder="Tell the community about yourself…"
              {...inputBase}
              h="80px"
              py="10px"
              resize="none"
              maxW="640px"
              lineHeight="24px"
            />

            <VStack align="start" gap="8px" w="100%" maxW="576px">
              <HStack gap="10px" w="100%">
                <Box color="gray.500" flexShrink={0}>
                  <LuGithub size={18} />
                </Box>
                <Input
                  value={github}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setGithub(e.target.value)
                  }
                  placeholder="https://github.com/username"
                  {...inputBase}
                  h="36px"
                />
              </HStack>

              <HStack gap="10px" w="100%">
                <Box color="gray.500" flexShrink={0}>
                  <LuLinkedin size={18} />
                </Box>
                <Input
                  value={linkedin}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setLinkedin(e.target.value)
                  }
                  placeholder="https://linkedin.com/in/username"
                  {...inputBase}
                  h="36px"
                />
              </HStack>

              <HStack gap="10px" w="100%">
                <Box color="gray.500" flexShrink={0}>
                  <LuGlobe size={18} />
                </Box>
                <Input
                  value={website}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setWebsite(e.target.value)
                  }
                  placeholder="https://yourwebsite.com"
                  {...inputBase}
                  h="36px"
                />
              </HStack>
            </VStack>
          </VStack>

          {/* Buttons */}
          <HStack gap="12px" flexShrink={0} align="flex-start">
            <Button
              onClick={() => router.push(`/profile/${apiUser.id}`)}
              variant="outline"
              border="1px solid"
              borderColor="orange.400"
              borderRadius="14px"
              h="44px"
              px="20px"
              fontSize="sm"
              color="gray.900"
              bg="white"
              _hover={{ bg: 'orange.50' }}
              transition="background 0.15s"
              disabled={saving}
            >
              <HStack gap="6px">
                <LuX size={16} />
                <Text>Cancel</Text>
              </HStack>
            </Button>

            <Button
              onClick={handleSave}
              bg="orange.400"
              color="white"
              borderRadius="14px"
              h="44px"
              px="20px"
              fontSize="sm"
              fontWeight="normal"
              _hover={{ bg: 'orange.500' }}
              transition="background 0.15s"
              loading={saving}
            >
              <HStack gap="6px">
                <LuSave size={16} />
                <Text>Save Changes</Text>
              </HStack>
            </Button>
          </HStack>
        </HStack>

        {/* Two-column lower section */}
        <Flex gap="24px" align="start">
          {/* Left column */}
          <VStack w="344px" flexShrink={0} gap="16px" align="start">
            {/* Academic Information */}
            <Box bg="gray.100" borderRadius="13px" p="24px" w="100%">
              <VStack align="start" gap="16px" w="100%">
                <Text
                  fontSize="md"
                  fontWeight="bold"
                  color="gray.900"
                  lineHeight="30px"
                >
                  Academic Information
                </Text>

                <VStack align="start" gap="4px" w="100%">
                  <FieldLabel>Major</FieldLabel>
                  <Input
                    value={major}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setMajor(e.target.value)
                    }
                    placeholder="e.g., Computer Engineering"
                    {...inputBase}
                    h="43px"
                  />
                </VStack>

                <VStack align="start" gap="4px" w="100%">
                  <FieldLabel>Graduation Year</FieldLabel>
                  <Input
                    type="number"
                    value={gradYear}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setGradYear(e.target.value)
                    }
                    placeholder="e.g., 2026"
                    {...inputBase}
                    h="43px"
                  />
                </VStack>

                <VStack align="start" gap="8px" w="100%">
                  <FieldLabel>UF Courses</FieldLabel>
                  <HStack gap="8px" w="100%">
                    <Input
                      value={courseInput}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setCourseInput(e.target.value)
                      }
                      onKeyDown={(e: React.KeyboardEvent) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          addCourse();
                        }
                      }}
                      placeholder="e.g., COP4331"
                      {...inputBase}
                      h="40px"
                      flex={1}
                    />
                    <Button
                      onClick={addCourse}
                      bg="orange.400"
                      color="white"
                      borderRadius="10px"
                      h="40px"
                      px="14px"
                      fontSize="sm"
                      fontWeight="normal"
                      flexShrink={0}
                      _hover={{ bg: 'orange.500' }}
                      transition="background 0.15s"
                      minW="44px"
                    >
                      <LuPlus size={16} />
                    </Button>
                  </HStack>
                  <Wrap gap="8px">
                    {courses.map((course: string) => (
                      <HStack
                        key={course}
                        gap="4px"
                        bg="white"
                        border="1.6px solid"
                        borderColor="orange.200"
                        borderRadius="8px"
                        pl="10px"
                        pr="6px"
                        py="4px"
                      >
                        <Text fontSize="sm" color="gray.900" lineHeight="24px">
                          {course}
                        </Text>
                        <Box
                          as="button"
                          onClick={() => removeCourse(course)}
                          color="gray.400"
                          cursor="pointer"
                          display="flex"
                          alignItems="center"
                          _hover={{ color: 'gray.700' }}
                          transition="color 0.1s"
                        >
                          <LuX size={12} />
                        </Box>
                      </HStack>
                    ))}
                  </Wrap>
                </VStack>
              </VStack>
            </Box>

            {/* Account Settings */}
            <Box bg="gray.100" borderRadius="13px" p="24px" w="100%">
              <VStack align="start" gap="16px" w="100%">
                <Text
                  fontSize="md"
                  fontWeight="bold"
                  color="gray.900"
                  lineHeight="30px"
                >
                  Account Settings
                </Text>

                <VStack align="start" gap="4px" w="100%">
                  <FieldLabel>Email Address</FieldLabel>
                  <Box position="relative" w="100%">
                    <Box
                      position="absolute"
                      left="12px"
                      top="50%"
                      transform="translateY(-50%)"
                      color="gray.400"
                      pointerEvents="none"
                    >
                      <LuMail size={16} />
                    </Box>
                    <Input
                      type="email"
                      value={apiUser.email}
                      readOnly
                      disabled
                      {...inputBase}
                      h="43px"
                      pl="38px"
                      opacity={0.6}
                      cursor="not-allowed"
                    />
                  </Box>
                </VStack>

                <VStack align="start" gap="12px" w="100%">
                  <Text
                    fontSize="sm"
                    fontWeight="bold"
                    color="gray.700"
                    lineHeight="24px"
                  >
                    Change Password
                  </Text>

                  <VStack align="start" gap="4px" w="100%">
                    <FieldLabel>Current Password</FieldLabel>
                    <PasswordField
                      placeholder="Enter current password"
                      value={currentPw}
                      onChange={setCurrentPw}
                    />
                  </VStack>

                  <VStack align="start" gap="4px" w="100%">
                    <FieldLabel>New Password</FieldLabel>
                    <PasswordField
                      placeholder="Enter new password (min 12 chars)"
                      value={newPw}
                      onChange={setNewPw}
                    />
                  </VStack>

                  <VStack align="start" gap="4px" w="100%">
                    <FieldLabel>Confirm New Password</FieldLabel>
                    <PasswordField
                      placeholder="Confirm new password"
                      value={confirmPw}
                      onChange={setConfirmPw}
                    />
                  </VStack>

                  {pwError && (
                    <Text fontSize="xs" color="red.500" lineHeight="20px">
                      {pwError}
                    </Text>
                  )}
                  {pwSuccess && (
                    <Text fontSize="xs" color="green.600" lineHeight="20px">
                      Password changed successfully.
                    </Text>
                  )}

                  <Button
                    onClick={handleChangePassword}
                    disabled={pwButtonDisabled}
                    w="100%"
                    border="1px solid"
                    borderColor={pwButtonDisabled ? 'gray.200' : 'orange.400'}
                    borderRadius="10px"
                    h="40px"
                    fontSize="sm"
                    color={pwButtonDisabled ? 'gray.400' : 'gray.900'}
                    bg="white"
                    _hover={pwButtonDisabled ? {} : { bg: 'orange.50' }}
                    transition="background 0.15s, border-color 0.15s, color 0.15s"
                    cursor={pwButtonDisabled ? 'not-allowed' : 'pointer'}
                    opacity={pwButtonDisabled ? 0.5 : 1}
                  >
                    <HStack gap="6px">
                      <LuShieldCheck size={15} />
                      <Text>Change Password</Text>
                    </HStack>
                  </Button>
                </VStack>
              </VStack>
            </Box>
          </VStack>

          {/* Right column */}
          <VStack flex={1} align="start" gap="32px" minW={0}>
            {/* Skills */}
            <VStack align="start" gap="16px" w="100%">
              <Text
                fontSize="md"
                fontWeight="bold"
                color="gray.900"
                lineHeight="30px"
              >
                Skills
              </Text>

              <Box bg="gray.100" borderRadius="13px" p="16px" w="100%">
                <HStack gap="8px">
                  <Input
                    value={skillInput}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setSkillInput(e.target.value)
                    }
                    onKeyDown={(e: React.KeyboardEvent) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addSkill();
                      }
                    }}
                    placeholder="Add a skill (e.g., React, Python…)"
                    {...inputBase}
                    h="43px"
                    flex={1}
                  />
                  <Button
                    onClick={addSkill}
                    bg="orange.400"
                    color="white"
                    borderRadius="10px"
                    h="43px"
                    px="20px"
                    fontSize="sm"
                    fontWeight="normal"
                    flexShrink={0}
                    _hover={{ bg: 'orange.500' }}
                    transition="background 0.15s"
                  >
                    <HStack gap="6px">
                      <LuPlus size={16} />
                      <Text>Add</Text>
                    </HStack>
                  </Button>
                </HStack>
              </Box>

              <Wrap gap="8px">
                {skills.map((skill: string) => (
                  <HStack
                    key={skill}
                    gap="4px"
                    bg="rgba(251,146,60,0.1)"
                    border="1.6px solid"
                    borderColor="orange.400"
                    borderRadius="10px"
                    pl="16px"
                    pr="10px"
                    py="8px"
                  >
                    <Text fontSize="sm" color="orange.400" lineHeight="24px">
                      {skill}
                    </Text>
                    <Box
                      as="button"
                      onClick={() => removeSkill(skill)}
                      color="orange.300"
                      cursor="pointer"
                      display="flex"
                      alignItems="center"
                      _hover={{ color: 'orange.500' }}
                      transition="color 0.1s"
                    >
                      <LuX size={12} />
                    </Box>
                  </HStack>
                ))}
              </Wrap>
            </VStack>

            {/* Projects (read-only — edit from individual project pages) */}
            <VStack align="start" gap="8px" w="100%">
              <Text
                fontSize="md"
                fontWeight="bold"
                color="gray.900"
                lineHeight="30px"
              >
                Projects
              </Text>
              <Text fontSize="sm" color="gray.400" lineHeight="24px">
                Manage your projects from the profile view or individual project
                pages.
              </Text>
            </VStack>
          </VStack>
        </Flex>
      </Box>
    </Box>
  );
}
