'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Flex,
  HStack,
  VStack,
  Text,
  Button,
  Wrap,
  SimpleGrid,
  Avatar,
  Input,
  Textarea,
} from '@chakra-ui/react';
import {
  LuX,
  LuSave,
  LuGraduationCap,
  LuBookOpen,
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
import { Navbar } from '@/components/Navbar';
import { ProfileProjectCard } from '@/components/ProfileProjectCard';
import { mockProfile, mockProfileProjects } from '@/data/mock-profile';

/* ── shared input style ─────────────────────────────────────── */
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

/* ── RoleBadge (same as profile page) ──────────────────────── */
function RoleBadge({ role }: { role: 'student' | 'faculty' }) {
  const Icon = role === 'faculty' ? LuBookOpen : LuGraduationCap;
  const label = role === 'faculty' ? 'Faculty' : 'Student';
  return (
    <HStack
      gap="6px"
      bg="rgba(251,146,60,0.1)"
      border="1.6px solid"
      borderColor="orange.400"
      borderRadius="full"
      px="12px"
      py="4px"
      display="inline-flex"
      flexShrink={0}
    >
      <Box color="orange.400">
        <Icon size={14} />
      </Box>
      <Text fontSize="xs" color="orange.400" fontWeight="medium">
        {label}
      </Text>
    </HStack>
  );
}

/* ── FieldLabel ─────────────────────────────────────────────── */
function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <Text fontSize="sm" color="gray.500" lineHeight="24px">
      {children}
    </Text>
  );
}

/* ── PasswordField (controlled) ─────────────────────────────── */
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

/* ── main page ──────────────────────────────────────────────── */
export default function EditProfilePage() {
  const router = useRouter();
  // Initialize profile from localStorage when available so edits persist across navigations.
  const getInitialProfile = () => {
    try {
      const raw = localStorage.getItem('gatorrank_profile');
      if (raw) return JSON.parse(raw);
    } catch {
      // ignore and fall back to mock
    }
    return mockProfile;
  };

  const initialProfile =
    typeof window !== 'undefined' ? getInitialProfile() : mockProfile;
  const profile = initialProfile;

  /* avatar */
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setAvatarPreview(URL.createObjectURL(file));
  };

  /* profile form state (initialized from saved profile if present) */
  const [name, setName] = useState(initialProfile.name);
  const [bio, setBio] = useState(initialProfile.bio);
  const [github, setGithub] = useState(initialProfile.socials?.github ?? '');
  const [linkedin, setLinkedin] = useState(
    initialProfile.socials?.linkedin ?? '',
  );
  const [website, setWebsite] = useState(initialProfile.socials?.website ?? '');
  const [major, setMajor] = useState(initialProfile.major);
  const [gradYear, setGradYear] = useState(
    String(initialProfile.graduationYear),
  );

  const [courses, setCourses] = useState<string[]>(
    initialProfile.courses ?? [],
  );
  const [courseInput, setCourseInput] = useState('');
  const addCourse = () => {
    if (courseInput.trim()) {
      setCourses((p: string[]) => [...p, courseInput.trim()]);
      setCourseInput('');
    }
  };
  const removeCourse = (c: string) =>
    setCourses((p: string[]) => p.filter((x) => x !== c));

  const [skills, setSkills] = useState<string[]>(initialProfile.skills ?? []);
  const [skillInput, setSkillInput] = useState('');
  const addSkill = () => {
    if (skillInput.trim()) {
      setSkills((p: string[]) => [...p, skillInput.trim()]);
      setSkillInput('');
    }
  };
  const removeSkill = (s: string) => setSkills((p) => p.filter((x) => x !== s));

  /* password state */
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [pwError, setPwError] = useState('');
  const [pwSuccess, setPwSuccess] = useState(false);

  const pwButtonDisabled = !currentPw || !newPw || !confirmPw;

  const handleChangePassword = () => {
    setPwError('');
    setPwSuccess(false);
    if (newPw !== confirmPw) {
      setPwError('New passwords do not match.');
      return;
    }
    if (newPw.length < 6) {
      setPwError('New password must be at least 6 characters.');
      return;
    }
    // TODO: replace with real API call once auth is set up
    setPwSuccess(true);
    setCurrentPw('');
    setNewPw('');
    setConfirmPw('');
  };

  /* save handler — writes to localStorage then navigates */
  const handleSave = () => {
    const updated = {
      ...profile,
      name,
      bio,
      socials: {
        github: github || undefined,
        linkedin: linkedin || undefined,
        website: website || undefined,
      },
      major,
      graduationYear: Number(gradYear) || profile.graduationYear,
      courses,
      skills,
    };
    localStorage.setItem('gatorrank_profile', JSON.stringify(updated));
    router.push('/profile');
  };

  return (
    <Box minH="100vh" bg="white">
      <Navbar />

      {/* Hidden file input for avatar upload */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleAvatarChange}
      />

      <Box px="36px" pt="32px" pb="64px" maxW="1280px" mx="auto">
        {/* ── Profile hero ──────────────────────────────────── */}
        <HStack gap="24px" mb="40px" align="flex-start">
          {/* Avatar with camera overlay */}
          <Box
            position="relative"
            w="96px"
            h="96px"
            flexShrink={0}
            cursor="pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <Avatar.Root
              w="96px"
              h="96px"
              borderRadius="full"
              overflow="hidden"
            >
              <Avatar.Fallback
                name={profile.name}
                bg="gray.300"
                color="gray.700"
                fontSize="xl"
                fontWeight="bold"
              />
              {(avatarPreview ?? profile.avatarUrl) && (
                <Avatar.Image src={avatarPreview ?? profile.avatarUrl} />
              )}
            </Avatar.Root>
            {/* Upload overlay */}
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
            {/* Name input + role badge */}
            <HStack gap="12px" align="center" w="100%" flexWrap="wrap">
              <Input
                value={name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setName(e.target.value)
                }
                {...inputBase}
                fontSize="xl"
                fontWeight="bold"
                h="47px"
                maxW="400px"
                lineHeight="32px"
              />
              <RoleBadge role={profile.role} />
            </HStack>

            {/* Bio textarea */}
            <Textarea
              value={bio}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                setBio(e.target.value)
              }
              {...inputBase}
              h="80px"
              py="10px"
              resize="none"
              maxW="640px"
              lineHeight="24px"
            />

            {/* Social inputs */}
            <VStack align="start" gap="8px" w="100%" maxW="576px">
              {/* GitHub */}
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

              {/* LinkedIn */}
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

              {/* Website */}
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

          {/* Action buttons — pinned right, top-aligned */}
          <HStack gap="12px" flexShrink={0} align="flex-start">
            <Button
              onClick={() => router.push('/profile')}
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
            >
              <HStack gap="6px">
                <LuSave size={16} />
                <Text>Save Changes</Text>
              </HStack>
            </Button>
          </HStack>
        </HStack>

        {/* ── Two-column lower section ──────────────────────── */}
        <Flex gap="24px" align="start">
          {/* Left column */}
          <VStack w="344px" flexShrink={0} gap="16px" align="start">
            {/* Academic Information card */}
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

                {/* Major */}
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

                {/* Graduation Year */}
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

                {/* UF Courses */}
                <VStack align="start" gap="8px" w="100%">
                  <FieldLabel>UF Courses</FieldLabel>

                  {/* Tag input row */}
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

                  {/* Course pills */}
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

            {/* Account Settings card */}
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

                {/* Email */}
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
                      defaultValue="luiscabrera@ufl.edu"
                      disabled
                      {...inputBase}
                      h="43px"
                      pl="38px"
                      opacity={0.6}
                      cursor="not-allowed"
                    />
                  </Box>
                </VStack>

                {/* Change Password section */}
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
                      placeholder="Enter new password"
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

                  {/* Feedback messages */}
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

                  {/* Change Password button */}
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

              {/* Skill tag input */}
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
                    placeholder="Add a skill (e.g., React, Python...)"
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

              {/* Skill pills */}
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

            {/* Projects (read-only) */}
            <VStack align="start" gap="16px" w="100%">
              <Text
                fontSize="md"
                fontWeight="bold"
                color="gray.900"
                lineHeight="30px"
              >
                Projects
              </Text>
              <SimpleGrid columns={3} gap="16px" w="100%">
                {mockProfileProjects.map((project) => (
                  <ProfileProjectCard key={project.id} project={project} />
                ))}
              </SimpleGrid>
            </VStack>
          </VStack>
        </Flex>
      </Box>
    </Box>
  );
}
