'use client';

import { useState } from 'react';
import {
  Box,
  Button,
  HStack,
  Input,
  Text,
  VStack,
  Wrap,
} from '@chakra-ui/react';
import {
  LuLock,
  LuEye,
  LuEyeOff,
  LuPlus,
  LuX,
  LuMail,
  LuShieldCheck,
} from 'react-icons/lu';

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
  inputBase,
}: {
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  inputBase: Record<string, unknown>;
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

interface ProfileEditColumnsProps {
  inputBase: Record<string, unknown>;
  major: string;
  gradYear: string;
  courseInput: string;
  courses: string[];
  email: string;
  currentPw: string;
  newPw: string;
  confirmPw: string;
  pwError: string;
  pwSuccess: boolean;
  pwButtonDisabled: boolean;
  skillInput: string;
  skills: string[];
  onMajorChange: (value: string) => void;
  onGradYearChange: (value: string) => void;
  onCourseInputChange: (value: string) => void;
  onAddCourse: () => void;
  onRemoveCourse: (course: string) => void;
  onCurrentPwChange: (value: string) => void;
  onNewPwChange: (value: string) => void;
  onConfirmPwChange: (value: string) => void;
  onChangePassword: () => void;
  onSkillInputChange: (value: string) => void;
  onAddSkill: () => void;
  onRemoveSkill: (skill: string) => void;
}

export function ProfileEditColumns({
  inputBase,
  major,
  gradYear,
  courseInput,
  courses,
  email,
  currentPw,
  newPw,
  confirmPw,
  pwError,
  pwSuccess,
  pwButtonDisabled,
  skillInput,
  skills,
  onMajorChange,
  onGradYearChange,
  onCourseInputChange,
  onAddCourse,
  onRemoveCourse,
  onCurrentPwChange,
  onNewPwChange,
  onConfirmPwChange,
  onChangePassword,
  onSkillInputChange,
  onAddSkill,
  onRemoveSkill,
}: ProfileEditColumnsProps) {
  return (
    <FlexSection>
      <VStack w="344px" flexShrink={0} gap="16px" align="start">
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
                  onMajorChange(e.target.value)
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
                  onGradYearChange(e.target.value)
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
                    onCourseInputChange(e.target.value)
                  }
                  onKeyDown={(e: React.KeyboardEvent) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      onAddCourse();
                    }
                  }}
                  placeholder="e.g., COP4331"
                  {...inputBase}
                  h="40px"
                  flex={1}
                />
                <Button
                  onClick={onAddCourse}
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
                      onClick={() => onRemoveCourse(course)}
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
                  value={email}
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
                  onChange={onCurrentPwChange}
                  inputBase={inputBase}
                />
              </VStack>

              <VStack align="start" gap="4px" w="100%">
                <FieldLabel>New Password</FieldLabel>
                <PasswordField
                  placeholder="Enter new password (min 12 chars)"
                  value={newPw}
                  onChange={onNewPwChange}
                  inputBase={inputBase}
                />
              </VStack>

              <VStack align="start" gap="4px" w="100%">
                <FieldLabel>Confirm New Password</FieldLabel>
                <PasswordField
                  placeholder="Confirm new password"
                  value={confirmPw}
                  onChange={onConfirmPwChange}
                  inputBase={inputBase}
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
                onClick={onChangePassword}
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

      <VStack flex={1} align="start" gap="32px" minW={0}>
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
                  onSkillInputChange(e.target.value)
                }
                onKeyDown={(e: React.KeyboardEvent) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    onAddSkill();
                  }
                }}
                placeholder="Add a skill (e.g., React, Python…)"
                {...inputBase}
                h="43px"
                flex={1}
              />
              <Button
                onClick={onAddSkill}
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
                  onClick={() => onRemoveSkill(skill)}
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
    </FlexSection>
  );
}

function FlexSection({ children }: { children: React.ReactNode }) {
  return (
    <Box as="div" display="flex" gap="24px" alignItems="flex-start">
      {children}
    </Box>
  );
}
